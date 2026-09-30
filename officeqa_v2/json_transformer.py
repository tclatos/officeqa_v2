"""Convert Databricks OfficeQA Pro V2 parsed JSON documents to structured Markdown.

Takes parsed JSON files with `document.elements` (containing layout-aware text,
section headers, titles, and HTML tables) and generates Markdown files structured
for hierarchical Document Graph ingestion:
  - Document Title: `# {document_basename}`
  - Page Headings: `## Page {page_number}` (1-indexed matching PDF pages)
  - Section Headings: `### {header}`
  - Tables: converted via `convert_html_table(table_html, table_expanded=True)`
    with rowspan/colspan expansion into Markdown tables, retaining structured
    HTML for complex unflattenable tables.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from genai_tk.extra.markdownize.table_processor import convert_html_table
from loguru import logger


def _get_element_page_id(element: dict[str, Any]) -> int:
    """Extract primary 0-indexed page_id from element bbox, default to 0."""
    bboxes = element.get("bbox")
    if isinstance(bboxes, list) and bboxes:
        first = bboxes[0]
        if isinstance(first, dict) and "page_id" in first:
            val = first["page_id"]
            if isinstance(val, (int, float)):
                return int(val)
    return 0


def _get_element_sort_key(element: dict[str, Any]) -> tuple[int, float, float, str]:
    """Sort elements by page_id, y0 coordinate, x0 coordinate, and id."""
    page_id = _get_element_page_id(element)
    bboxes = element.get("bbox")
    y0 = 0.0
    x0 = 0.0
    if isinstance(bboxes, list) and bboxes:
        coord = bboxes[0].get("coord")
        if isinstance(coord, list) and len(coord) >= 2:
            x0 = float(coord[0])
            y0 = float(coord[1])
    raw_id = element.get("id", "")
    elem_id = str(raw_id) if raw_id is not None else ""
    return (page_id, y0, x0, elem_id)


def parse_json_document_to_markdown(
    json_path: Path | str,
    *,
    table_expanded: bool = True,
) -> str:
    """Read a Databricks parsed JSON file and render it as structured Markdown.

    Args:
        json_path: Path to the parsed JSON file.
        table_expanded: Whether to expand rowspan/colspan HTML tables to Markdown.

    Returns:
        Structured Markdown string with page/section headers and converted tables.
    """
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    doc_data = data.get("document") or {}
    elements: list[dict[str, Any]] = doc_data.get("elements") or []
    doc_stem = path.stem

    if not elements:
        logger.warning("No elements found in parsed JSON: {}", path)
        return f"# {doc_stem}\n\n(No parsed elements in document)\n"

    # Sort elements sequentially in reading order (by page then y0, x0)
    sorted_elements = sorted(elements, key=_get_element_sort_key)

    md_lines: list[str] = [f"# {doc_stem}", ""]
    current_page_id: int | None = None

    for elem in sorted_elements:
        elem_type = elem.get("type", "text")
        content = elem.get("content", "")

        # Skip headers, footers, and page numbers to avoid polluting section text
        if elem_type in ("page_header", "page_footer", "page_number"):
            continue

        page_id = _get_element_page_id(elem)
        # Check if page changed (convert 0-indexed page_id to 1-indexed PDF page number)
        if page_id != current_page_id:
            current_page_id = page_id
            pdf_page_num = page_id + 1
            md_lines.append(f"## Page {pdf_page_num}")
            md_lines.append("")

        if elem_type == "figure":
            # For figures, emit description if available
            desc = elem.get("description")
            if desc and str(desc).strip():
                md_lines.append(f"> **[Figure on Page {page_id + 1}]**: {desc.strip()}")
                md_lines.append("")
            continue

        if not content or not str(content).strip():
            continue

        raw_str = str(content).strip()

        if elem_type == "table":
            if "<table" in raw_str.lower():
                try:
                    converted_table = convert_html_table(raw_str, table_expanded=table_expanded)
                    md_lines.append(converted_table)
                except Exception as exc:
                    logger.debug("Failed converting HTML table on page {}: {}", page_id + 1, exc)
                    md_lines.append(raw_str)
            else:
                md_lines.append(raw_str)
            md_lines.append("")

        elif elem_type == "title":
            clean_title = re.sub(r"[\r\n]+", " ", raw_str).strip()
            md_lines.append(f"### {clean_title}")
            md_lines.append("")

        elif elem_type == "section_header":
            clean_header = re.sub(r"[\r\n]+", " ", raw_str).strip()
            md_lines.append(f"#### {clean_header}")
            md_lines.append("")

        elif elem_type == "footnote":
            md_lines.append(f"*Footnote:* {raw_str}")
            md_lines.append("")

        elif elem_type == "caption":
            md_lines.append(f"*Caption:* {raw_str}")
            md_lines.append("")

        else:
            # text and any other unrecognized element types
            md_lines.append(raw_str)
            md_lines.append("")

    return "\n".join(md_lines)


def convert_parsed_json_file(
    json_path: Path | str,
    output_md_path: Path | str,
    *,
    table_expanded: bool = True,
    force: bool = False,
) -> Path:
    """Convert a parsed JSON file to Markdown and write to disk."""
    src = Path(json_path)
    dst = Path(output_md_path)
    if dst.exists() and not force and dst.stat().st_size > 0:
        logger.debug("Markdown already exists: {}", dst)
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)
    md_content = parse_json_document_to_markdown(src, table_expanded=table_expanded)
    dst.write_text(md_content, encoding="utf-8")
    logger.info("Converted JSON -> Markdown ({} bytes) -> {}", len(md_content), dst)
    return dst
