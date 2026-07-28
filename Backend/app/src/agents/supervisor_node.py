from typing import Literal

from langchain_classic import hub
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from Backend.app.src.config import get_llm
from Backend.app.src.graph.state import GraphState
from Backend.app.src.graph.state_utils import get_state
from Backend.app.src.logs.logger import logger
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

class SupervisorDecision(BaseModel):
    decision: Literal[
        "planner",
        "reporter",
        "end",
    ] = Field(description="Next workflow node.")

    feedback: str = Field(
        description="""
Actionable feedback.

If planner:
Describe what additional execution or analysis is required.

If reporter:
Describe how the report should be improved.

If end:
Briefly explain why the report fully satisfies the request.
"""
    )

from langsmith import Client

client = Client()

SYSTEM_PROMPT = client.pull_prompt("sup_sp").format()

def supervisor_node(state: GraphState) -> GraphState:
    logger.info("Supervisor evaluating workflow.")

    review_count = state.get("supervisor_review_count", 0)
    max_reviews = state.get("max_supervisor_reviews", 2)

    if state.get("final_report") and review_count >= max_reviews:

        logger.warning("Maximum supervisor reviews reached.")

        return {
            "supervisor_decision": "end",
            "supervisor_feedback": "Maximum supervisor review limit reached.",
        }

    # --------------------------------------------------
    # Stage 1
    # --------------------------------------------------

    if not state.get("final_report"):

        state_summary = f"""
USER REQUEST

{get_state(state, "user_query", "")}

INITIALIZE OUTPUT

Dataset Schema:
{get_state(state, "df_schema", "")}

Memory Usage:
{get_state(state, "memory_usage_mb", "Unknown")} MB
"""

    # --------------------------------------------------
    # Stage 2
    # --------------------------------------------------

    else:

        state_summary = f"""
USER REQUEST

{get_state(state, "user_query", "")}

PLANNER OUTPUT

{get_state(state, "plan", "No execution plan.")}

GENERATED CHARTS

{get_state(state, "chart_files", [])}

EXECUTION STATUS

{get_state(state, "execution_status", "")}

REPORTER OUTPUT

{get_state(state, "final_report", "")}
"""

    try:

        router = get_llm(state.get("api_key"), state.get("model")).with_structured_output(SupervisorDecision)

        decision = router.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=state_summary),
            ]
        )

    except Exception as exc:

        logger.exception("Supervisor routing failed.")

        return {
            "supervisor_decision": "planner",
            "supervisor_feedback": "Supervisor routing failed.",
            "fatal_error": str(exc),
        }

    updates = {
        "supervisor_decision": decision.decision,
        "supervisor_feedback": decision.feedback,
    }

    if state.get("final_report"):
        updates["supervisor_review_count"] = review_count + 1

    logger.info(
        "Supervisor selected -> %s | %s",
        decision.decision,
        decision.feedback,
    )

    return updates