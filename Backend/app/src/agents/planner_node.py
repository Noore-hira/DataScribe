from __future__ import annotations

import json
import re
from json import JSONDecodeError

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig  # 1. Added import for secure config

from Backend.app.src.config import get_llm
from Backend.app.src.graph.state import GraphState
from Backend.app.src.graph.state_utils import require_state
from Backend.app.src.logs.logger import logger
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

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
SYSTEM_PROMPT = client.pull_prompt("planner_sp").format()

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
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    reraise=True,
)
def generate_plan(messages, llm_instance) -> ExecutionPlan:

    response = llm_instance.invoke(messages)

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

# 2. Added config: RunnableConfig to the parameters
def planner_node(state: GraphState, config: RunnableConfig) -> GraphState:

    logger.info("Planner started.")
    
    # 3. Extract the API key SECURELY from the config, not the state
    api_key = config.get("configurable", {}).get("api_key")

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
            ],
            # 4. Pass the securely extracted api_key to your LLM configuration
            get_llm(api_key, state.get("model")),
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

        "planner_metrics": {
            "analysis_tasks": len(plan.analysis_tasks),
            "visualization_tasks": len(plan.visualization_tasks),
            "statistical_tasks": len(plan.statistical_tasks),
        }
    }