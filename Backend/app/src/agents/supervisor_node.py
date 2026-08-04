from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langsmith import Client
from pydantic import BaseModel, Field

from Backend.app.src.config import get_llm
from Backend.app.src.graph.state import GraphState
from Backend.app.src.graph.state_utils import get_state
from Backend.app.src.logs.logger import logger

load_dotenv()
client = Client()


class SupervisorDecision(BaseModel):
    decision: Literal["planner", "reporter", "end"] = Field(
        description="Next workflow node."
    )

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


SYSTEM_PROMPT = client.pull_prompt("sup_sp").format()


def supervisor_node(state: GraphState, config: RunnableConfig) -> GraphState:
    logger.info("Supervisor evaluating workflow.")

    api_key = config.get("configurable", {}).get("api_key")

    # ==================================================
    # Stage 1 : Before execution
    # ==================================================

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

        try:
            router = (
                get_llm(api_key, state.get("model"))
                .with_structured_output(SupervisorDecision)
            )

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

        logger.info(
            "Supervisor selected -> %s | %s",
            decision.decision,
            decision.feedback,
        )

        return {
            "supervisor_decision": decision.decision,
            "supervisor_feedback": decision.feedback,
        }

    # ==================================================
    # Stage 2 : Final report review
    # ==================================================

    state_summary = f"""
USER REQUEST

{get_state(state, "user_query", "")}

PLANNER OUTPUT

{get_state(state, "plan", "No execution plan.")}

GENERATED CHARTS

{get_state(state, "chart_files", [])}

EXECUTION STATUS

{get_state(state, "execution_status", "")}

CRITIC VERDICT

{get_state(state, "critic_verdict", "")}

REPORTER OUTPUT

{get_state(state, "final_report", "")}
"""

    try:
        router = (
            get_llm(api_key, state.get("model"))
            .with_structured_output(SupervisorDecision)
        )

        review = router.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=state_summary),
            ]
        )

    except Exception:
        logger.exception("Supervisor review failed.")

        return {
            "supervisor_decision": "end",
            "supervisor_feedback": "Supervisor review failed.",
        }

    logger.info(
        "Supervisor reviewed final report. Ending workflow. Feedback: %s",
        review.feedback,
    )

    return {
        # Always terminate after reviewing the report
        "supervisor_decision": "end",
        "supervisor_feedback": review.feedback,
    }