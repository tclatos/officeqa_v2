"""OfficeQA Pro V2 dataset adapter for US Federal Accounts of Receipts and Expenditures.

Re-exports OfficeQAV2Adapter from adapter_v2.py as the primary adapter for officeqa_v2.
"""

from __future__ import annotations

from officeqa_v2.adapter_v2 import (
    DATASET_ID_V2,
    OFFICEQA_V2_JUDGE_RUBRIC,
    OfficeQAV2Adapter,
    parse_v2_source_docs,
    parse_v2_source_files,
)

# Primary adapter alias for the v2 benchmark
OfficeQAAdapter = OfficeQAV2Adapter

__all__ = [
    "DATASET_ID_V2",
    "OFFICEQA_V2_JUDGE_RUBRIC",
    "OfficeQAAdapter",
    "OfficeQAV2Adapter",
    "parse_v2_source_docs",
    "parse_v2_source_files",
]
