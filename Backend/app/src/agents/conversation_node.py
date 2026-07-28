from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from Backend.app.src.config import get_llm
from Backend.app.src.graph.state import GraphState
from Backend.app.src.logs.logger import logger
from Backend.app.src.memory.memory_manager import update_conversation_memory
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

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

SYSTEM_PROMPT = client.pull_prompt("con_sp").format()

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

    router = get_llm(state.get("api_key"), state.get("model")).with_structured_output(
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
        "conversation_metrics": {
            "route": decision.decision
            }
    }