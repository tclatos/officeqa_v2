"""Python code executor and calculator tools for OfficeQA.

Provides safe in-process AST Python execution with NumPy, SciPy, and Pandas
for quantitative, statistical, and financial calculations (e.g., OLS regressions,
Box-Cox transformations, geometric means, CAGR, inflation adjustments).
"""

from __future__ import annotations

from genai_tk.agents.tools.python_executor import (
    PythonExecutorTool,
    create_python_executor_tool,
    create_python_executor_tools,
)
from langchain_core.tools import BaseTool


def create_calculator_tools(
    authorized_imports: list[str] | None = None,
    timeout_seconds: int | None = 30,
) -> list[BaseTool]:
    """Factory returning Python code execution tools configured for OfficeQA.

    Authorizes numpy, pandas, scipy, and standard math/statistics libraries.
    """
    default_imports = ["numpy", "pandas", "scipy", "math", "statistics", "re", "json"]
    effective_imports = list(set((authorized_imports or []) + default_imports))
    return create_python_executor_tools(
        additional_authorized_imports=effective_imports,
        timeout_seconds=timeout_seconds,
    )


__all__ = [
    "PythonExecutorTool",
    "create_calculator_tools",
    "create_python_executor_tool",
    "create_python_executor_tools",
]
