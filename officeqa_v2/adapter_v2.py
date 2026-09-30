"""OfficeQA Pro V2 dataset adapter for US Federal Accounts of Receipts and Expenditures."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
from genai_graph.bench.adapters.base import (
    BaseBenchmarkAdapter,
    download_hf_file,
)
from genai_graph.bench.models import BenchQuestion
from loguru import logger

DATASET_ID_V2 = "databricks/officeqa-pro-v2"

OFFICEQA_V2_JUDGE_RUBRIC = """\
You are a strict-but-fair grader for OfficeQA Pro V2, a benchmark on US Federal Accounts of Receipts and Expenditures (1793–2024).
Compare the agent's answer to the gold answer using the gold evidence, provenance, and source files.

Return ONLY a JSON object with exactly these keys:
{
  "correctness": "correct" | "partial" | "incorrect",
  "numeric_match": true | false | null,
  "groundedness": "grounded" | "partial" | "ungrounded",
  "error_category": "missing_ocr_or_visual_chart" | "calculation_or_math_error" | "retrieval_or_lookup_error" | "halted_or_empty_response" | null,
  "rationale": "<one sentence>"
}

Ground truth answers come in three shapes:
1. Bare numbers (e.g. 21.58, 0.866)
2. Currencies with formatting (e.g. $7,046,001.98, $12,345)
3. Bracketed label/value lists (e.g. [Massachusetts, 0.866], [42, 105])

Equivalence rules:
- Numerical accuracy: rounding differences within reasonable decimal precision (e.g. 0.866 vs 0.8660) are correct.
- Currency: dollar signs, commas, and negative parentheses (e.g. (1,234) for -1,234) should be normalized.
- Multi-number or bracketed lists: both the text label and numeric value must match. Order matters in ordered list answers.
- The agent answer is CORRECT if the gold answer, or its numeric equivalence, is clearly stated as the final answer.
- "partial" = right direction or partial list, but inaccurate values or incomplete elements.
- "incorrect" = wrong value, wrong entity, or empty/failed response.
- "error_category" when not correct:
  * "missing_ocr_or_visual_chart": question requires reading an unparsed figure/chart.
  * "calculation_or_math_error": agent retrieved correct numbers but made formula, arithmetic, or unit scale error.
  * "retrieval_or_lookup_error": retrieved wrong year, wrong table, wrong column, or failed to navigate multi-document chain.
  * "halted_or_empty_response": agent exceeded tool iterations or aborted without answer.
"""


def parse_v2_source_files(val: str | None) -> list[str]:
    """Parse source_files string into a list of normalized doc stems (without .txt/.json/.pdf)."""
    if not val or not isinstance(val, str):
        return []
    # Can be semicolon or newline separated
    raw_entries = re.split(r"[;\n\r]+", val)
    cleaned: list[str] = []
    for raw in raw_entries:
        s = raw.strip()
        if not s:
            continue
        if s.endswith((".txt", ".pdf", ".json", ".md")):
            stem = Path(s).stem
        else:
            stem = s
        if stem and stem not in cleaned:
            cleaned.append(stem)
    return cleaned


def parse_v2_source_docs(val: str | None) -> list[dict[str, str]]:
    """Parse pipe/semicolon delimited source_docs string into structured records."""
    if not val or not isinstance(val, str):
        return []
    records: list[dict[str, str]] = []
    for chunk in val.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        entry: dict[str, str] = {}
        for part in chunk.split("|"):
            if "=" in part:
                k, v = part.split("=", 1)
                entry[k.strip()] = v.strip()
        if entry:
            records.append(entry)
    return records


class OfficeQAV2Adapter(BaseBenchmarkAdapter):
    """Adapter for databricks/officeqa-pro-v2 using parsed JSON documents."""

    name: str = "officeqa_v2"

    def load_dataset(self, split: str | None = None, cache_dir: Path | None = None) -> list[BenchQuestion]:
        """Load Databricks OfficeQA Pro V2 dataset (90 questions) and convert to BenchQuestion models."""
        target_dir = cache_dir or (Path.cwd() / "data" / "officeqa_v2")
        target_dir.mkdir(parents=True, exist_ok=True)
        cache_file = target_dir / "officeqa_pro_v2.parquet"

        if cache_file.exists():
            logger.info("Loading cached OfficeQA Pro V2 dataset from {}", cache_file)
            df = pd.read_parquet(cache_file)
        else:
            logger.info("Downloading {}/officeqa_pro_v2.csv from Hugging Face", DATASET_ID_V2)
            csv_path = download_hf_file(
                repo_id=DATASET_ID_V2,
                filename="officeqa_pro_v2.csv",
                repo_type="dataset",
            )
            df = pd.read_csv(csv_path)
            df.to_parquet(cache_file, index=False)
            logger.info("Cached {} rows to {}", len(df), cache_file)

        questions: list[BenchQuestion] = []
        for idx, row in df.iterrows():
            q_id = str(row.get("uid") if pd.notna(row.get("uid")) else f"v2_{idx}")
            raw_sources = str(row.get("source_files", "")) if pd.notna(row.get("source_files")) else ""
            doc_names = parse_v2_source_files(raw_sources)
            doc_name = doc_names[0] if doc_names else "unknown"
            q_text = str(row.get("question", ""))
            gold_ans = str(row.get("answer", ""))

            raw_source_docs = str(row.get("source_docs", "")) if pd.notna(row.get("source_docs")) else ""
            parsed_docs = parse_v2_source_docs(raw_source_docs)

            evidence = [
                f"{d.get('corpus_file', '')} p.{d.get('pdf_page_number', '')} ({d.get('year', '')}): {d.get('description', '')}"
                for d in parsed_docs
                if d.get("corpus_file")
            ]

            metadata: dict[str, Any] = {
                "officeqa_id": q_id,
                "uid": q_id,
                "source_files": raw_sources,
                "doc_names": doc_names,
                "source_docs": raw_source_docs,
                "parsed_source_docs": parsed_docs,
            }

            questions.append(
                BenchQuestion(
                    id=q_id,
                    doc_name=doc_name,
                    doc_names=doc_names,
                    question=q_text,
                    gold_answer=gold_ans,
                    evidence=evidence,
                    justification=None,
                    metadata=metadata,
                )
            )
        return questions

    def get_referenced_doc_stems(self, cache_dir: Path | None = None) -> list[str]:
        """Return the unique set of document stems referenced across all benchmark questions."""
        questions = self.load_dataset(cache_dir=cache_dir)
        stems: set[str] = set()
        for q in questions:
            for name in q.doc_names:
                stems.add(name)
        return sorted(stems)

    def fetch_document(self, doc_name: str, output_dir: Path) -> Path:
        """Download parsed JSON document from OfficeQA Pro V2 dataset repository."""
        output_dir.mkdir(parents=True, exist_ok=True)
        clean_name = doc_name[:-5] if doc_name.endswith(".json") else doc_name
        target = output_dir / f"{clean_name}.json"
        if target.exists() and target.stat().st_size > 0:
            return target

        try:
            downloaded = download_hf_file(
                repo_id=DATASET_ID_V2,
                filename=f"parsed_corpus/jsons/{clean_name}.json",
                repo_type="dataset",
                output_dir=output_dir,
            )
            if downloaded != target and downloaded.exists():
                import shutil

                shutil.copy2(downloaded, target)
            return target
        except Exception as exc:
            logger.warning("Could not fetch parsed JSON from HF for {}: {}. Creating placeholder.", clean_name, exc)
            target.write_text(f'{{"error": "Failed to fetch {clean_name}: {exc}"}}', encoding="utf-8")
            return target

    def get_judge_rubric(self) -> str:
        return OFFICEQA_V2_JUDGE_RUBRIC
