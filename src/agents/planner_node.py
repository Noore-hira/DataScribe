from __future__ import annotations

import json
import re
from json import JSONDecodeError

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm
from src.graph.state import GraphState
from src.graph.state_utils import require_state
from src.logs.logger import logger


# ==========================================================
# Planner Schema
# ==========================================================

class ExecutionPlan(BaseModel):

    summary: str = ""

    analysis_tasks: list[str] = Field(default_factory=list)

    visualization_tasks: list[str] = Field(default_factory=list)

    statistical_tasks: list[str] = Field(default_factory=list)

    execution_order: list[str] = Field(default_factory=list)


# ==========================================================
# Planner Prompt
# ==========================================================

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

Typical execution orders

Analysis only

["Analysis"]

Charts only

["Visualization"]

Analysis + Charts

["Analysis","Visualization"]

If a section has no tasks return an empty list.
"""


JSON_INSTRUCTIONS = """
Return ONLY valid JSON.

Schema

{
    "summary": string,
    "analysis_tasks": [string],
    "visualization_tasks": [string],
    "statistical_tasks": [string],
    "execution_order": [string]
}

Rules

- Return ONLY JSON.
- No markdown.
- No explanations.
- No code fences.
- No extra keys.
- Empty sections should be [].
"""


# ==========================================================
# Planner Generator
# ==========================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    reraise=True,
)
def generate_plan(messages) -> ExecutionPlan:

    response = llm.invoke(messages)

    text = response.content.strip()

    # Remove markdown fences
    if text.startswith("```"):

        text = (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    # Extract JSON if model added extra text
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        text = match.group(0)

    try:

        data = json.loads(text)

        plan = ExecutionPlan.model_validate(data)

    except JSONDecodeError:

        logger.error("Planner returned invalid JSON.")
        logger.error(text)
        raise

    except ValidationError:

        logger.error("Planner JSON failed validation.")
        logger.error(text)
        raise

    # Planner shouldn't return an empty plan
    if not (
        plan.analysis_tasks
        or plan.visualization_tasks
        or plan.statistical_tasks
    ):
        raise ValueError("Planner returned an empty execution plan.")

    return plan


# ==========================================================
# Planner Node
# ==========================================================

def planner_node(state: GraphState) -> GraphState:

    logger.info("Planner started.")

    user_query = require_state(state, "user_query")
    schema = require_state(state, "df_schema")

    try:

        plan = generate_plan(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT
                    + "\n\n"
                    + JSON_INSTRUCTIONS
                ),
                HumanMessage(
                    content=f"""
User Request

{user_query}

Dataset Schema

{schema}

Supervisor Feedback

{state.get("supervisor_feedback", "")}

Current Execution Plan

{state.get("plan", "")}
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
        "Planner created %d analysis task(s), "
        "%d statistical task(s), "
        "%d visualization task(s).",
        len(plan.analysis_tasks),
        len(plan.statistical_tasks),
        len(plan.visualization_tasks),
    )

    formatted_plan = f"""
Summary:
{plan.summary}

Analysis Tasks:
{chr(10).join(f"- {task}" for task in plan.analysis_tasks)}

Statistical Tasks:
{chr(10).join(f"- {task}" for task in plan.statistical_tasks)}

Visualization Tasks:
{chr(10).join(f"- {task}" for task in plan.visualization_tasks)}

Execution Order:
{" → ".join(plan.execution_order)}
""".strip()

    # Safety: remove accidental code blocks
    formatted_plan = re.sub(
        r"```(?:python)?\s*.*?```",
        "",
        formatted_plan,
        flags=re.DOTALL,
    ).strip()

    return {
        "plan": formatted_plan,
    }