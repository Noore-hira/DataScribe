import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

from src.config import llm
from src.graph.state import GraphState
from src.logs.logger import logger


# --------------------------------------------------------
# Output Schema
# --------------------------------------------------------

class CriticVerdict(BaseModel):
    verdict: Literal["pass", "fail", "abort"] = Field(
        description="Whether another programmer iteration is required."
    )

    feedback: str = Field(
        description="Actionable feedback for the programmer."
    )


# --------------------------------------------------------
# JSON Instructions
# --------------------------------------------------------

JSON_INSTRUCTIONS = """
Return ONLY valid JSON.

Rules:

- Return ONLY JSON.
- No markdown.
- No explanation.
- No thinking.
- No text before or after the JSON.

Valid values for verdict:

- pass
- fail
- abort

Example:

{
    "verdict": "pass",
    "feedback": "The requested analysis has been completed successfully."
}
"""


# --------------------------------------------------------
# Prompt
# --------------------------------------------------------

SYSTEM_PROMPT = """
You are the QA Reviewer of DataScribe.

Your ONLY responsibility is deciding whether another Programmer
iteration is required.

Review:

- User request
- Execution plan
- Generated code
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

Return ABORT only if another retry is pointless.

Do NOT fail because:

- Better charts are possible.
- More statistics could be added.
- Code style could be improved.
- Another implementation exists.

If returning FAIL, explain exactly what the Programmer
should fix.

Keep feedback concise (1-2 sentences).
"""


# --------------------------------------------------------
# LLM Reviewer
# --------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
def review_execution(review: str) -> CriticVerdict:

    response = llm.invoke(
        [
            SystemMessage(
                content=SYSTEM_PROMPT
                + "\n\n"
                + JSON_INSTRUCTIONS
            ),
            HumanMessage(content=review),
        ]
    )

    text = response.content.strip()

    # Remove markdown if the model ignores instructions
    if text.startswith("```"):
        text = (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    try:
        return CriticVerdict.model_validate(
            json.loads(text)
        )

    except Exception:

        logger.error("Invalid critic JSON:")
        logger.error(text)

        raise


# --------------------------------------------------------
# Node
# --------------------------------------------------------

def critic_node(state: GraphState) -> GraphState:

    logger.info("Critic started.")

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    # ----------------------------------------------------
    # Retry limit reached
    # ----------------------------------------------------

    if retry_count >= max_retries:

        logger.warning("Maximum retries reached.")

        return {
            "critic_verdict": "abort",
            "critic_feedback": "Maximum retry limit reached.",
            "critic_metrics": {
                "verdict": "abort",
                "retry": retry_count,
            },
        }

    # ----------------------------------------------------
    # Execution failed immediately
    # ----------------------------------------------------

    if state.get("execution_status") == "failed":

        logger.warning("Execution failed.")

        return {
            "critic_verdict": "fail",
            "critic_feedback": state.get(
                "execution_error",
                "Execution failed.",
            ),
            "retry_count": retry_count + 1,
            "critic_metrics": {
                "verdict": "fail",
                "retry": retry_count + 1,
            },
        }

    # ----------------------------------------------------
    # Build review prompt
    # ----------------------------------------------------

    review = f"""
User Request

{state.get("user_query", "")}


Execution Plan

{state.get("plan", "")}


Generated Code

{state.get("generated_code", "")}


Execution Output

{state.get("execution_output", "")}


Execution Error

{state.get("execution_error", "")}


Generated Charts

{state.get("chart_files", [])}
"""

    # ----------------------------------------------------
    # Ask LLM
    # ----------------------------------------------------

    try:

        verdict = review_execution(review)

    except Exception:

        logger.exception("Critic failed.")

        return {
            "critic_verdict": "fail",
            "critic_feedback": "Critic failed to evaluate the execution.",
            "retry_count": retry_count + 1,
            "critic_metrics": {
                "verdict": "fail",
                "retry": retry_count + 1,
            },
        }

    logger.info(
        "Critic verdict: %s",
        verdict.verdict.upper(),
    )

    # ----------------------------------------------------
    # Needs another iteration
    # ----------------------------------------------------

    if verdict.verdict == "fail":

        return {
            "critic_verdict": "fail",
            "critic_feedback": verdict.feedback,
            "retry_count": retry_count + 1,
            "critic_metrics": {
                "verdict": "fail",
                "retry": retry_count + 1,
            },
        }

    # ----------------------------------------------------
    # Abort
    # ----------------------------------------------------

    if verdict.verdict == "abort":

        return {
            "critic_verdict": "abort",
            "critic_feedback": verdict.feedback,
            "critic_metrics": {
                "verdict": "abort",
                "retry": retry_count,
            },
        }

    # ----------------------------------------------------
    # Pass
    # ----------------------------------------------------

    return {
        "critic_verdict": "pass",
        "critic_feedback": verdict.feedback,
        "critic_metrics": {
            "verdict": "pass",
            "retry": retry_count,
        },
    }