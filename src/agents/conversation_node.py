from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm
from src.graph.state import GraphState
from src.logs.logger import logger
from src.memory.memory_manager import update_conversation_memory


class ConversationDecision(BaseModel):
    decision: Literal[
        "answer",
        "initialize",
        "reject",
    ] = Field(
        description="Next workflow action."
    )

    response: str = Field(
        description="Assistant response when decision is answer or reject."
    )


SYSTEM_PROMPT = """
You are the Conversation Agent of DataScribe.

Your ONLY responsibility is deciding whether the data-analysis workflow
should run.

You NEVER:

- perform dataset analysis
- execute Python
- create charts
- calculate statistics
- generate reports

You may ONLY answer using the supplied conversation memory.

====================================================
Decision: answer
====================================================

Choose "answer" when the user's request can be answered from the supplied
conversation memory.

Examples:

- Greetings
- Thanks
- Goodbye
- Who are you?
- What can DataScribe do?
- Summarize the previous report.
- What charts were generated?
- What was the total sales?
- What insights did we find?
- What did we discuss earlier?

Never invent information.

If the requested information does not exist in the supplied memory,
do NOT guess.

====================================================
Decision: reject
====================================================

Choose "reject" for requests unrelated to DataScribe.

Examples:

- Tell me a joke.
- Write a poem.
- Explain quantum mechanics.
- Who won FIFA?
- What is the capital of France?

====================================================
Decision: initialize
====================================================

Choose "initialize" whenever the request requires NEW dataset processing.

Examples:

- Analyze my dataset
- Build dashboard
- Create charts
- Find correlations
- Detect anomalies
- Forecast sales
- Train a model
- Generate report
- Show dataset columns
- Show missing values
- Calculate statistics

If the answer requires information from the currently uploaded dataset,
choose initialize.

If no dataset has been uploaded yet,
still choose initialize.

Return ONLY the structured output.
"""


def conversation_node(state: GraphState):

    logger.info("Conversation agent started.")

    user_query = state["user_query"]

    session_summary = state.get(
        "session_summary",
        "",
    )

    recent_messages = state.get(
        "recent_messages",
        [],
    )

    # --------------------------------------------------
    # Build memory context
    # --------------------------------------------------

    memory_context = ""

    if session_summary:

        memory_context += f"""

Session Summary

{session_summary}
"""

    if recent_messages:

        memory_context += f"""

Recent Conversation

{recent_messages}
"""

    router = llm.with_structured_output(
        ConversationDecision
    )

    decision = router.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""
Current User Query

{user_query}

{memory_context}
"""
            ),
        ]
    )

    logger.info(
        "Conversation decision -> %s",
        decision.decision,
    )

    # --------------------------------------------------
    # Route to workflow
    # --------------------------------------------------

    if decision.decision == "initialize":

        return {
            "conversation_route": "initialize",
        }


    memory_updates = update_conversation_memory(
    state=state,
    user_query=user_query,
    assistant_response=decision.response,
    )

    return {
        "conversation_route": decision.decision,
        "final_report": decision.response,
        **memory_updates,
    }