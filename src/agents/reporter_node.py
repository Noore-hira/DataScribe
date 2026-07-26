import os

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import get_llm
from src.graph.state import GraphState
from src.graph.state_utils import get_state, require_state
from src.logs.logger import logger
from src.memory.memory_manager import update_analysis_memory


SYSTEM_PROMPT = """
You are an expert Data Science Technical Writer.

Create a professional markdown report.

The report should contain:

# Executive Summary

# Dataset Overview

# Analysis Results

# Visualization Summary

Describe the generated charts.

Do not generate Python.

Do not mention internal agents.

If execution was only partially successful,
clearly explain which parts completed successfully
and which parts could not be completed.

Use ONLY the provided execution results.
"""


def reporter_node(state: GraphState) -> GraphState:

    logger.info("Reporter started.")

    if state.get("fatal_error"):
        return {
            "final_report": state["fatal_error"]
        }

    user_query = require_state(state, "user_query")
    schema = require_state(state, "df_schema")

    chart_files = get_state(
        state,
        "chart_files",
        [],
    )

    user_prompt = f"""
User Request

{user_query}

Execution Plan

{get_state(state, "plan", "")}

Dataset Schema

{schema}

Supervisor Feedback

{state.get("supervisor_feedback", "")}

Execution Output

{get_state(state, "execution_output", "")}

Generated Charts

{chart_files}

Critic Verdict

{get_state(state, "critic_verdict", "pass")}

Critic Feedback

{get_state(state, "critic_feedback", "")}
"""

    try:

        response = get_llm(state.get("api_key"), state.get("model")).invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )

        report = response.content

    except Exception:

        logger.exception("Reporter failed.")

        report = get_state(
            state,
            "execution_output",
            "",
        )

    # ==========================================================
    # Generated Visualizations
    # ==========================================================

    charts_md = ""

    if chart_files:

        charts_md += "\n\n# Generated Visualizations\n"

        for path in chart_files:

            filename = os.path.basename(path)

            if filename.endswith(".html"):

                charts_md += f"""
## {filename}

<iframe
src="{path}"
width="100%"
height="600"
style="border:none;">
</iframe>

"""

            elif filename.endswith(".png"):

                charts_md += f"""
## {filename}

![{filename}]({path})

"""

    # ==========================================================
    # Partial completion warning
    # ==========================================================

    warning_md = ""

    if get_state(state, "critic_verdict") == "abort":

        warning_md = f"""

---

# ⚠ Partial Completion

The requested task could not be fully completed after
**{get_state(state, "retry_count", 0)}** retry attempt(s).

Reason:

{get_state(state, "critic_feedback", "")}

The successfully generated outputs have been included in this report.

"""

    final_report = report + warning_md + charts_md

    # ==========================================================
    # Update conversation memory
    # ==========================================================

    memory_updates = update_analysis_memory(
        state,
        report,
    )

    logger.info("Final report generated.")

    return {
        "final_report": report + warning_md + charts_md,
        **memory_updates,

        "reporter_metrics": {

        "charts": len(chart_files),

        "report_length": len(report)

    }
        }