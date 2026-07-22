import re

from src.config import llm_for_pg
from src.graph.state import GraphState
from src.graph.state_utils import get_state, require_state
from src.logs.logger import logger

programmer_instructions = (
    "You are a Senior Python Data Scientist responsible for writing robust Pandas analysis code.\n\n"
    "CRITICAL RULES:\n"
    "1. Your ONLY task is to generate executable Python analysis code.\n"
    "2. The dataset is already loaded as `global_df`.\n"
    "3. NEVER read files or reload the dataset.\n"
    "4. NEVER use import statements. `pd`, `pl`, `sns`, and `plt` are already available.\n"
    "5. Before any analysis, clean the dataset by handling missing values and parsing date columns when appropriate.\n"
    "6. Use print() for every statistic or insight so it appears in stdout.\n"
    "7. If reviewer feedback is provided, fix ALL reported issues.\n"
    "8. Do not repeat previous mistakes.\n"
    "9. Return ONLY Python code wrapped inside ```python ... ```."
)


def programmer_node(state: GraphState):
    """Generate or revise analysis code."""

    logger.info("Programmer node started.")

    plan = require_state(state, "plan")
    schema = require_state(state, "df_schema")

    runtime_error = ""
    critic_feedback = ""

    if get_state(state, "has_error", False):
        runtime_error = get_state(state, "execution_output", "")

    if get_state(state, "critic_feedback"):
        critic_feedback = get_state(state, "critic_feedback")

    prompt = f"""
Execution Plan:
{plan}

Dataset Schema:
{schema}
"""

    if runtime_error:
        prompt += f"""

Previous Runtime Error:
{runtime_error}

Correct the cause of this failure.
"""

    if critic_feedback:
        prompt += f"""

Reviewer Feedback:
{critic_feedback}

Revise the code to address EVERY issue above before generating the new solution.
"""

    try:
        response = llm_for_pg.invoke(
            [
                {
                    "role": "system",
                    "content": programmer_instructions,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

    except Exception as exc:
        logger.exception("Programmer LLM invocation failed.")

        return {
            "fatal_error": (
                f"The analysis model is unavailable "
                f"({exc.__class__.__name__})."
            )
        }

    raw_output = response.content

    code_match = re.search(
        r"```python\s*(.*?)```",
        raw_output,
        re.DOTALL,
    )

    if code_match:
        code = code_match.group(1).strip()
    else:
        logger.warning("LLM returned no Python code block.")
        code = "print('No valid code generated.')"

    logger.info(
        "Programmer generated %d lines of code.",
        len(code.splitlines()),
    )

    return {
        "current_code": code,
    }