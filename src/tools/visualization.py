import os
import shutil

import matplotlib
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import pandas as pd

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from data_frame import load_dataframe
from src.config import llm_for_pg
from src.logs.logger import logger
from src.tools.code_executor import (
    execute_generated_code,
    extract_python_code,
)
from src.tools.safe_execution import normalize_visualization_artifacts

matplotlib.use("Agg")
plt.style.use("dark_background")


@tool
def create_visualization_tool(
    plot_description: str,
    run_id: str = "default",
) -> dict:
    """
    Generate visualizations for the loaded dataframe.
    """

    logger.info("Visualization Tool started.")

    artifact_root = os.environ.get(
        "LANGGRAPH_ARTIFACTS_DIR",
        "charts",
    )

    charts_dir = os.path.join(
        artifact_root,
        run_id,
    )

    # -----------------------------
    # Fresh artifact directory
    # -----------------------------

    if os.path.exists(charts_dir):
        shutil.rmtree(charts_dir)

    os.makedirs(
        charts_dir,
        exist_ok=True,
    )

    global_df = load_dataframe()

    system_prompt = f"""
You are a Senior Python Data Visualization Engineer.

Generate ONLY Python code.

Rules

1. The dataframe already exists as `global_df`.

2. Never import anything.

3. Available objects

- px
- go
- sns
- plt

4. Prefer Plotly.

5. Never call

plt.show()
fig.show()

6. Every figure MUST be saved inside

{charts_dir}

7. Plotly

fig.write_html(...)

8. Matplotlib

plt.savefig(...)

9. Generate every requested chart.

10. Return ONLY a Python code block.
"""

    user_prompt = f"""
Dataset Columns

{list(global_df.columns)}

Dataset Schema

{global_df.dtypes}

Visualization Request

{plot_description}
"""

    # ----------------------------------------------------

    try:

        response = llm_for_pg.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

    except Exception as exc:

        logger.exception("Visualization model failed.")

        return {
            "status": "failed",
            "generated_code": "",
            "execution_output": "",
            "error": str(exc),
            "files": [],
        }

    code = extract_python_code(
        response.content
    )

    code = normalize_visualization_artifacts(
        code,
        charts_dir,
    )

    result = execute_generated_code(
        code=code,
        exec_globals={
            "global_df": global_df,
            "plt": plt,
            "pd":pd,
            "sns": sns,
            "px": px,
            "go": go,
        },
        artifact_dir=charts_dir,
        task_name="visualization",
    )

    # ----------------------------------------------------
    # Execution failed
    # ----------------------------------------------------

    if result["status"] == "failed":

        logger.error("Visualization execution failed.")

        return {
            "status": "failed",
            "generated_code": result.get("code", ""),
            "execution_output": result.get("output", ""),
            "error": result.get("error", ""),
            "files": [],
        }

    # ----------------------------------------------------
    # Collect generated charts
    # ----------------------------------------------------

    saved_files = sorted(
        os.path.join(charts_dir, f).replace("\\", "/")
        for f in os.listdir(charts_dir)
    )

    if not saved_files:

        logger.warning(
            "Visualization succeeded but produced no charts."
        )

        return {
            "status": "failed",
            "generated_code": result.get("code", ""),
            "execution_output": result.get("output", ""),
            "error": "No chart files were generated.",
            "files": [],
        }

    logger.info(
        "Visualization Tool finished with %d chart(s).",
        len(saved_files),
    )

    return {
        "status": "success",
        "generated_code": result.get("code", ""),
        "execution_output": result.get("output", ""),
        "error": "",
        "files": saved_files,
    }