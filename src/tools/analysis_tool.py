import numpy as np
import pandas as pd
import polars as pl

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from data_frame import load_dataframe
from src.config import llm_for_pg
from src.logs.logger import logger
from src.tools.code_executor import execute_llm_code


@tool
def create_analysis_tool(
    analysis_request: str,
) -> dict:
    """
    Perform dataframe analysis, cleaning and statistical computations.
    """

    logger.info("Analysis Tool started.")

    global_df = load_dataframe()

    system_prompt = """
You are a Senior Python Data Scientist.

Generate ONLY Python code.

Rules

1. The dataframe already exists as `global_df`.

2. NEVER load any files.

3. NEVER import anything.

4. Available objects

- global_df
- pd
- np
- pl

5. Always start with

df = global_df.copy()

Never modify global_df.

6. Data cleaning

- Parse datetime columns whenever appropriate.
- Fill numeric missing values using the median.
- Fill categorical missing values using "Unknown".

7. Numeric operations

Whenever computing:

- correlation
- covariance
- statistics
- distributions
- regression
- numerical summaries

always use

numeric_df = df.select_dtypes(include="number")

Never call

df.corr()

Always call

numeric_df.corr()

8. Before correlation

if numeric_df.shape[1] >= 2:
    print(numeric_df.corr())

9. If no numeric columns exist,
print a meaningful message instead of raising an exception.

10. Print every important result.

11. Never create charts.

12. Never call plt.show().

13. Return ONLY one Python code block.
"""

    user_prompt = f"""
Dataset Columns

{list(global_df.columns)}

Dataset Schema

{global_df.dtypes}

Analysis Request

{analysis_request}
"""

    # -----------------------------------------------------

    try:

        response = llm_for_pg.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

    except Exception as exc:

        logger.exception("Analysis model failed.")

        return {
            "status": "failed",
            "generated_code": "",
            "execution_output": "",
            "error": str(exc),
        }

    # -----------------------------------------------------

    result = execute_llm_code(
        llm_output=response.content,
        exec_globals={
            "global_df": global_df,
            "pd": pd,
            "np": np,
            "pl": pl,
        },
        task_name="analysis",
    )

    if result["status"] == "failed":

        logger.error("Analysis execution failed.")

        return {
            "status": "failed",
            "generated_code": result.get("code", ""),
            "execution_output": result.get("output", ""),
            "error": result.get("error", ""),
        }

    logger.info("Analysis Tool finished successfully.")

    return {
        "status": "success",
        "generated_code": result.get("code", ""),
        "execution_output": result.get("output", ""),
        "error": "",
    }