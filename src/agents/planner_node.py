import re
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm
from src.graph.state import GraphState
from src.graph.state_utils import require_state
from src.logs.logger import logger


class ExecutionPlan(BaseModel):
    summary: str = Field(
        description="High-level summary of the requested task."
    )

    analysis_tasks: list[str] = Field(
        description="Analysis or data-cleaning tasks that must be completed."
    )

    visualization_tasks: list[str] = Field(
        description="Charts or visualizations that should be created."
    )

    statistical_tasks: list[str] = Field(
        description="Statistical calculations or aggregations required."
    )

    execution_order: list[str] = Field(
        description="Ordered list of work stages."
    )


SYSTEM_PROMPT = """
You are the Planner Agent of an AI Data Science system.

Your ONLY responsibility is to create an execution plan.

DO NOT:

- write Python
- write pseudocode
- mention libraries
- mention imports
- explain implementation
- load datasets
- describe algorithms

The programmer agent will perform implementation.

The visualization tool will create charts.

Create a structured roadmap only.

Rules:

• analysis_tasks should contain every required analysis.

• visualization_tasks should only contain charts explicitly requested.

• statistical_tasks should contain required statistics.

• execution_order should describe the work sequence.

Typical execution orders:

Analysis only:
["Analysis"]

Charts only:
["Visualization"]

Analysis + Charts:
["Analysis", "Visualization"]
"""


def planner_node(state: GraphState):
    """Generate a structured execution plan."""

    logger.info("Planner started.")

    user_query = require_state(state, "user_query")
    schema = require_state(state, "df_schema")

    try:

        planner = llm.with_structured_output(ExecutionPlan)

        plan: ExecutionPlan = planner.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(
                    content=f"""
User Request

{user_query}

Dataset Schema

{schema}

Supervisor Feedback

{state.get("supervisor_feedback","")}

Current Execution Plan

{state.get("plan","")}
"""
                ),
            ]
        )

    except Exception as exc:

        logger.exception("Planner failed.")

        message = (
            f"Planning model unavailable: "
            f"{exc.__class__.__name__}"
        )

        return {
            "fatal_error": message,
            "final_report": message,
        }

    logger.info(
        "Planner created %d analysis task(s) and %d visualization task(s).",
        len(plan.analysis_tasks),
        len(plan.visualization_tasks),
    )

    formatted_plan = f"""
Summary:
{plan.summary}

Analysis Tasks:
{chr(10).join(f"- {task}" for task in plan.analysis_tasks)}

Visualization Tasks:
{chr(10).join(f"- {task}" for task in plan.visualization_tasks)}

Statistical Tasks:
{chr(10).join(f"- {task}" for task in plan.statistical_tasks)}

Execution Order:
{" → ".join(plan.execution_order)}
""".strip()

    # Safety: remove accidental fenced code blocks if the model ignores instructions.
    formatted_plan = re.sub(
        r"```(?:python)?\s*.*?```",
        "",
        formatted_plan,
        flags=re.DOTALL,
    ).strip()

    return {
        "plan": formatted_plan,
    }