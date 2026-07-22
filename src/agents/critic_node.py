from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from data_frame import load_dataframe
from src.config import llm
from src.graph.state import GraphState
from src.graph.state_utils import get_state, require_state
from src.logs.logger import logger


class CriticVerdict(BaseModel):
    verdict: Literal["pass", "fail"] = Field(
        description="Whether the programmer's solution satisfies the requirements."
    )
    critique: str = Field(
        description="Concrete feedback for the programmer."
    )


SYSTEM_PROMPT = """
You are a Senior Python Data Science Code Reviewer.

Your ONLY responsibility is to review the PROGRAMMER agent's work.

Evaluate ALL of the following:

1. Does the generated code satisfy the execution plan?
2. Does it answer the user's request?
3. Are all requested analyses and statistical calculations included?
4. Is the existing dataframe `global_df` used correctly?
5. Does the code avoid loading the dataset again?
6. Does it avoid unnecessary modification of the dataframe?
7. Is there redundant, inefficient, or unnecessary code?
8. If execution failed, identify the exact reason and explain how the programmer should fix it.

Guidelines:

- Ignore formatting and markdown.
- Ignore visualization quality.
- Focus ONLY on the generated analysis code.
- Return FAIL if execution failed.
- Return FAIL if requested analyses are missing.
- Return PASS only if everything is complete.

Your feedback should be specific and actionable.
"""


def critic_node(state: GraphState):
    """Review the programmer's solution after execution."""

    logger.info("Critic node started.")

    # Required state
    user_query = require_state(state, "user_query")
    schema = require_state(state, "df_schema")
    plan = require_state(state, "plan")
    code = require_state(state, "current_code")

    # Optional state
    has_error = get_state(state, "has_error", False)
    retry_count = get_state(state, "retry_count", 0)
    execution_output = get_state(state, "execution_output", "")

    # Deterministic fallback
    if has_error and retry_count >= 3:
        logger.warning(
            "Maximum retries reached. Falling back to dataset profiling."
        )

        dataframe = load_dataframe()

        message = (
            "The programmer could not produce executable analysis after "
            "three attempts.\n\n"
            f"Rows: {len(dataframe)}\n"
            f"Columns: {', '.join(dataframe.columns)}\n\n"
            "Missing Values:\n"
            f"{dataframe.isnull().sum().to_string()}\n\n"
            "Summary Statistics:\n"
            f"{dataframe.describe(include='all').to_string()}"
        )

        return {
            "has_error": False,
            "execution_output": message,
            "critic_verdict": "fail",
            "critic_feedback": "Maximum retries reached.",
        }

    review_input = f"""
User Query:
{user_query}

Dataset Schema:
{schema}

Execution Plan:
{plan}

Generated Code:
{code}

Execution Output:
{execution_output}

Execution Failed:
{has_error}
"""

    try:
        reviewer = llm.with_structured_output(CriticVerdict)

        verdict: CriticVerdict = reviewer.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=review_input),
            ]
        )

    except Exception:
        logger.exception("Critic LLM invocation failed.")

        return {
            "has_error": True,
            "critic_verdict": "fail",
            "critic_feedback": (
                "The reviewer model was unavailable. "
                "Please retry."
            ),
            "retry_count": retry_count + 1,
        }

    logger.info("Critic verdict: %s", verdict.verdict.upper())

    if verdict.verdict == "fail":
        logger.warning("Programmer revision requested.")

        return {
            "has_error": True,
            "critic_verdict": verdict.verdict,
            "critic_feedback": verdict.critique,
            "retry_count": retry_count + 1,
        }

    logger.info("Programmer solution approved.")

    return {
        "has_error": False,
        "critic_verdict": verdict.verdict,
        "critic_feedback": verdict.critique,
    }