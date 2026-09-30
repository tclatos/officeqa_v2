# OfficeQA Pro V2 Implementation & Benchmark Assessment Report

**Date**: 2026-09-30  
**Project**: [officeqa_v2](https://github.com/tclatos/officeqa_v2)  
**Authors**: Atos GenAI Engineering Team  
**Dataset Reference**: Databricks OfficeQA Pro V2 ([Hugging Face](https://huggingface.co/datasets/databricks/officeqa-pro-v2) & [Announcement Blog](https://www.databricks.com/blog/introducing-officeqa-pro-v2-new-benchmark-enterprise-grounded-reasoning))

---

## 1. Executive Summary

This report documents the implementation of the **OfficeQA Pro V2** benchmark pipeline in a newly scaffolded, dedicated project repository: [officeqa_v2](https://github.com/tclatos/officeqa_v2). 

Unlike OfficeQA Pro V1 (which relied on 697 U.S. Treasury Bulletins from 1939 to 2025), V2 challenges agentic systems with the **U.S. Federal Accounts of Receipts and Expenditures** across **232 years (1793–2024)**.

Key accomplishments:
1. **Zero-OCR Fast Pipeline**: Capitalized on Databricks' pre-parsed JSON corpus (`ai_parse`), downloading all **249 referenced source documents** (~433 MB) and bypassing costly OCR APIs.
2. **Layout-Aware Markdown Transformation**: Transformed all 249 JSON documents into structured Markdown (280 MB total) with 1-based page headers (`## Page N`) and expanded 2D table matrices handling complex merged rows and columns (`rowspan`/`colspan`).
3. **Dedicated Clean Repository**: Scaffolded and pushed [tclatos/officeqa_v2](https://github.com/tclatos/officeqa_v2) to GitHub, maintaining complete isolation from the V1 codebase.
4. **Dual Scoring Engine**: Vendored Databricks' official [reward.py](https://github.com/databricks/officeqa/blob/main/reward.py) reference implementation to perform exact deterministic matching (0.0% tolerance across currency, numbers, and bracketed lists) while preserving qualitative LLM-as-judge diagnostic rubrics.

---

## 2. Directory Structure & Key Paths

The new project is housed in `/home/tcl/prj/officeqa_v2`:

| Path | Purpose | Size / Count |
|---|---|---|
| `officeqa_v2/` | Core Python package (`adapter_v2.py`, `json_transformer.py`, `reward.py`, `commands/`, `tools/`) | Clean package root |
| `config/` | Application & benchmark profiles (`app_conf.yaml`, `bench.yaml`, `docgraph.yaml`, `agents.yaml`) | Central YAML config |
| `data/jsons/` | Downloaded parsed JSON documents from Hugging Face | 249 files (~433 MB) |
| `data/saved_markdown/` | Generated hierarchical Markdown documents ready for ingestion | 249 files (280 MB) |
| `data/kg/officeqa_v2.db` | Ladybug Knowledge Graph database (Folder, Document, Section nodes, BM25 FTS index) | In active build |
| `data/officeqa_pro_v2.parquet` | Cached benchmark dataset questions & metadata | 90 questions |
| `skills/custom/officeqa-v2-qa/` | Agent domain knowledge skill ([SKILL.md](skills/custom/officeqa-v2-qa/SKILL.md)) | 1793–2024 conventions |
| `reports/` | Engineering and evaluation reports | This document |

---

## 3. What Was Done

### 3.1. Dataset Ingestion & Adapter (`officeqa_v2/adapter_v2.py`)
- Created `OfficeQAV2Adapter` subclassing `BaseBenchmarkAdapter`.
- Loads the 90 questions from `databricks/officeqa-pro-v2` (`officeqa_pro_v2.csv`).
- Deduplicates and normalizes `source_files` into 249 distinct document stems across two centuries.
- Resolves per-document provenance from `source_docs` (including PDF page numbers and year tags).

### 3.2. JSON to Markdown Transformer (`officeqa_v2/json_transformer.py`)
- Ingests parsed JSON elements (`text`, `section_header`, `title`, `table`, `figure`, `footnote`).
- Sorts elements sequentially in reading order by page and spatial coordinates ($y_0, x_0$).
- Filters out non-content artifacts (`page_header`, `page_footer`, `page_number`).
- Formats figure visual descriptions as blockquotes (`> **[Figure on Page N]**: ...`).
- **Table Transformation**: Integrates with `genai_tk.extra.markdownize.table_processor`:
  - Simplifies HTML `<table>` elements into Markdown pipe tables.
  - Expands `rowspan` and `colspan` into uniform 2D rectangular matrices.
  - Falls back gracefully to structured HTML with dimension annotations for deeply nested tables.

### 3.3. Core Framework Extensions (`genai-graph`)
- Enhanced `genai_graph.bench.adapters.base.download_hf_file` to support authenticated Hugging Face hub resolution.
- Updated `genai_graph.bench.build_graph` with `find_source_file_path`, allowing benchmark pipelines to seamlessly discover `.json` files and route them through project-specific transformers.
- Extended `genai_graph.bench.judge.evaluate_single_run` and `BenchScoreRecord` to record deterministic `reward_score` alongside LLM-as-judge verdicts.
- Committed and pushed changes to `tclatos/genai-graph`.

### 3.4. Dual Evaluation Engine (`officeqa_v2/reward.py`)
- Vendored Databricks' official `reward.py` matching rules:
  - Exact numerical matching with 0.0% tolerance.
  - Currency normalization (`$7,046,001.98` $\rightarrow$ `7046001.98`, accounting `(1,234)` $\rightarrow$ `-1234`).
  - Single and multi-number bracketed lists (`[Massachusetts, 0.866]`).
  - Automatic extraction of `<FINAL_ANSWER>...</FINAL_ANSWER>` XML tags.

### 3.5. Domain Skill Authoring (`skills/custom/officeqa-v2-qa/SKILL.md`)
- Detailed the 4 core document naming conventions:
  - `govinfo_receipts__{YEAR}__{GPO_ID}` (1793–1893)
  - `combined_statement__historical__cs-{YEAR}` (1872–1994)
  - `combined_statement__transition__appendix{YY}__{SECTION}`
  - `combined_statement__modern__{YEAR}__{SECTION}` (2001–2024)
- Formalized historical ledger quirks:
  - "do." shorthand for ditto (carrying state/category from preceding row).
  - Priority rule: Always select the latest reported revised figure in subsequent annual editions over preliminary reports.
  - Calendar year (CY) vs. fiscal year (FY) transition in 1843 and 1976.

---

## 4. Benchmark Difficulty Assessment & Baseline Performance

OfficeQA Pro V2 is significantly more difficult than OfficeQA Pro V1:

1. **Massive Multi-Document Scope**:
   - V1 questions referenced an average of ~2 documents.
   - V2 questions reference a median of **5.5 documents (range 1–24)**; **74.4%** require 4 or more documents.
2. **Prior-Year Revisions**:
   - Financial figures are updated in subsequent editions. Agents that stop at the first matching document retrieve outdated preliminary numbers and score 0.
3. **Complex Quantitative Reasoning**:
   - Questions test advanced statistical and econometric operations: OLS linear regression trends, non-seasonal Theta forecasting, Box-Cox transformations, Gini coefficients, and multi-period geometric means.
4. **Strict Evaluation Metric**:
   - 0.0% tolerance exact match. Any extraneous commentary outside the `<FINAL_ANSWER>` tags or any slight unit mismatch produces a score of 0.

### Published Baseline Landscape

| Agent Harness | Model | Accuracy | Average Cost / Rollout |
|---|---|---|---|
| Claude Code | Claude 3.5 Sonnet | 15.6% | $5.01 |
| Codex | GPT-5.6 Sol | 33.3% | $4.70 |
| Baseline Frontier Average | Frontier Models | **37.5%** | $4.85 |
| Grounded Reasoning Cup | Competition Teams Average | **41.1%** | — |
| Databricks Genie | Claude Fable 5 / GPT-5.6 Terra | **52.8% – 60.0%** | $4.15 |
| Competition Winner | SOTA Custom Agent | **63.3%** | — |

---

## 5. Our Advantage & Strategic Recommendations

### 5.1. Why Our Stack Can Reach 55% – 65%+
1. **Vectorless Navigation Prevents Context Overflow**:
   - Standard frontier agents attempt to load full documents into context, looping and inflating costs up to $37 per question.
   - Our agent uses `get_folder_toc`, `get_document_toc`, and `search_sections` to navigate heading hierarchies, inspecting only necessary table sections.
2. **Table Structural Fidelity**:
   - Converting HTML tables into clean 2D Markdown tables with span expansion ensures numbers and column relationships remain unambiguous.
3. **Execution via `python_interpreter`**:
   - Offloading calculations (OLS, Theta method, EMA) to Python eliminates LLM math and rounding mistakes.

### 5.2. Recommendations to Outperform SOTA
1. **Two-Stage Multi-Document Extraction Protocol**:
   - Instruct the agent to construct an internal structured observation matrix before attempting math:
     ```markdown
     | Year | Document ID | Metric Value | Revision Status |
     | 1792 | ... | ... | Final |
     | 1793 | ... | ... | Revised |
     ```
   - Only after all years are assembled should the agent execute calculation in Python.
2. **Mandatory Prior-Year Check**:
   - When retrieving data for year $T$, verify if edition $T+1$ or $T+2$ revised the figure.
3. **Strict `<FINAL_ANSWER>` XML Tagging**:
   - Ensure the agent always concludes with `<FINAL_ANSWER>...</FINAL_ANSWER>` containing only the bare value, currency, or bracketed list.

---

## 6. Next Steps

1. **Finalize Knowledge Graph Build**:
   - Allow the active background build process to finish extracting outlines and indexing `data/kg/officeqa_v2.db`.
2. **Run 5-Question Smoke Test**:
   ```bash
   cd /home/tcl/prj/officeqa_v2
   uv run cli bench run --profile officeqa_v2 --limit 5
   ```
3. **Inspect Execution Trajectories**:
   ```bash
   uv run cli bench tui
   ```
4. **Execute Full 90-Question Benchmark**:
   ```bash
   uv run cli bench run --profile officeqa_v2
   uv run cli bench report --profile officeqa_v2
   ```
