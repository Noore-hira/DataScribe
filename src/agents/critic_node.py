from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.config import llm
from src.graph.state import GraphState
from src.logs.logger import logger


class CriticVerdict(BaseModel):
    verdict: Literal["pass", "fail", "abort"] = Field(
        description="Whether another programmer iteration is required."
    )

    feedback: str = Field(
        description="Short actionable feedback for the programmer."
    )


SYSTEM_PROMPT = """
You are the QA Reviewer of DataScribe.

Your ONLY responsibility is deciding whether another Programmer iteration is required.

Review:

- User request
- Execution plan
- Execution output
- Runtime errors
- Generated charts

Return PASS when:

- The requested analysis is complete.
- The requested visualizations exist.
- There are no execution errors.
- The user's request has been satisfied.

Return FAIL only when:

- Execution failed.
- Required analysis is missing.
- Required charts are missing.
- The user's request was not answered.

Do NOT fail because:

- Better charts are possible.
- More statistics could be added.
- Code style could be improve.
- Another implementation exists.

If returning FAIL, explain exactly what the Programmer should fix.
"""


def critic_node(state: GraphState) -> GraphState:

    logger.info("Critic started.")

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    # --------------------------------------------------
    # Stop retry loop
    # --------------------------------------------------

    if retry_count >= max_retries:

        logger.warning("Maximum retries reached.")

        return {
            "critic_verdict": "abort",
            "critic_feedback": "Maximum retry limit reached.",
        }

    # --------------------------------------------------
    # Runtime execution failed
    # --------------------------------------------------

    if state.get("execution_status") == "failed":

        logger.warning("Execution failed.")

        return {
            "critic_verdict": "fail",
            "critic_feedback": state.get(
                "execution_error",
                "Execution failed.",
            ),
            "retry_count": retry_count + 1,
        }

    # --------------------------------------------------
    # LLM validation
    # --------------------------------------------------

    review = f"""
User Request

{state.get("user_query","")}


Execution Plan

{state.get("plan","")}


Generated Code

{state.get("generated_code","")}


Execution Output

{state.get("execution_output","")}


Execution Error

{state.get("execution_error","")}


Generated Charts

{state.get("chart_files",[])}
"""

    reviewer = llm.with_structured_output(CriticVerdict)

    verdict = reviewer.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=review),
        ]
    )

    logger.info("Critic verdict: %s", verdict.verdict.upper())

    if verdict.verdict == "fail":

        return {
            "critic_verdict": "fail",
            "critic_feedback": verdict.feedback,
            "retry_count": retry_count + 1,
        }

    return {
        "critic_verdict": "pass",
        "critic_feedback": verdict.feedback,
    }