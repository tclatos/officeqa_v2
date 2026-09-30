---
name: officeqa-v2-qa
description: Answer OfficeQA Pro V2 questions across historical and modern U.S. Federal Accounts of Receipts and Expenditures (1793–2024) by navigating the Document Graph.
---

# OfficeQA Pro V2 Question Answering

You answer grounded analytical and numerical questions across two centuries (1793–2024) of U.S. Federal Accounts of Receipts and Expenditures, Combined Statements, and Congressional serial-set receipts publications.

---

## 1. Corpus Structure & Document Families

The benchmark corpus draws from four distinct document naming conventions:
- `govinfo_receipts__{YEAR}__{GPO_ID}`: Early receipts and expenditures (1793–1893). Historic typography (long-s, "ditto/do."), wide foldouts, verbose tabular descriptions.
- `combined_statement__historical__cs-{YEAR}`: Annual Combined Statements (1872–1994). T-accounts, ruled multi-column tables, introduction of fiscal years.
- `combined_statement__transition__appendix{YY}__{SECTION}`: Transition-era appendix reports.
- `combined_statement__modern__{YEAR}__{SECTION}`: Modern digital reports (2001–2024). Standardized sections, TAS symbol breakdowns.

---

## 2. Critical Historical Conventions & Rules

1. **"do." / "ditto" Interpretation**:
   - In 18th and 19th-century ledgers, "do." indicates "ditto", repeating the category, state, or office from the preceding non-empty line.
2. **Prior-Year Revised Figures vs. Preliminary Figures**:
   - When a series spans multiple years, **always use the latest revised figure** reported in subsequent annual editions rather than the first reported preliminary figure.
3. **Multi-Document Evidence Assembly**:
   - Most V2 questions require combining figures across 4 to 24 separate documents. Follow links systematically and record observations by year/document.
4. **Time Scoping**:
   - Note calendar year (CY) vs. fiscal year (FY). In 1843, the federal reporting period changed from calendar year ending Dec 31 to fiscal year ending June 30 (and later Sept 30 in 1976).
5. **Exact Answer Formatting**:
   - Always conclude your response with your final answer wrapped in `<FINAL_ANSWER>...</FINAL_ANSWER>` XML tags.
   - For bare numbers: `<FINAL_ANSWER>21.58</FINAL_ANSWER>`
   - For currency: `<FINAL_ANSWER>$7,046,001.98</FINAL_ANSWER>`
   - For label/value lists: `<FINAL_ANSWER>[Massachusetts, 0.866]</FINAL_ANSWER>`

---

## 3. Navigation & Tool Discipline

1. **Inspect Table of Contents**: Use `get_document_toc(document_id=...)` to identify relevant sections and tables.
2. **Keyword Search**: Use `search_sections(query=..., document_id=...)` with compact keywords (e.g. `"Collector of Customs"`, `"Outlays by Function"`, `"TAS"`).
3. **Paging & Slicing**: For wide or tall tables, use `start_line` and `max_lines` with `get_section_content` to inspect rows without context overflow.
4. **Calculation Precision**: Use `python_interpreter` for all regressions (OLS, exponential smoothing, moving averages, Theta method) and exact calculations.
