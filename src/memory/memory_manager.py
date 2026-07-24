from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm
from src.graph.state import GraphState


# ==========================================================
# Prompts
# ==========================================================

MEMORY_PROMPT = """
You are maintaining long-term conversation memory for a data analysis assistant.

Summarize ONLY the information that will help answer future user questions.

Include:

- User request
- Important findings
- Key statistics
- Important conclusions
- Charts that were generated

Do NOT include:

- Python code
- Internal implementation
- Agent names
- Temporary execution errors

Maximum 200 words.

Return only the summary.
"""


COMPRESS_MEMORY_PROMPT = """
You maintain conversation memory.

Merge and compress the following summaries.

Requirements

- Preserve important findings.
- Preserve statistics.
- Preserve user goals.
- Preserve generated visualizations.
- Remove repetition.

Maximum 300 words.

Return only the compressed summary.
"""


# ==========================================================
# LLM Memory Generation
# ==========================================================

def generate_memory_summary(
    *,
    user_query: str,
    execution_output: str,
    report: str,
    chart_files: list[str],
) -> str:
    """
    Generate a concise summary of the completed analysis.
    """

    try:

        response = llm.invoke(
            [
                SystemMessage(content=MEMORY_PROMPT),
                HumanMessage(
                    content=f"""
User Request

{user_query}

Execution Output

{execution_output}

Generated Report

{report}

Generated Charts

{chart_files}
"""
                ),
            ]
        )

        return response.content.strip()

    except Exception:

        return ""


def compress_memory(summary: str) -> str:
    """
    Compress long session memory.
    """

    try:

        response = llm.invoke(
            [
                SystemMessage(content=COMPRESS_MEMORY_PROMPT),
                HumanMessage(content=summary),
            ]
        )

        return response.content.strip()

    except Exception:

        return summary


# ==========================================================
# Recent Conversation
# ==========================================================

def update_recent_messages(
    recent_messages: list,
    user_query: str,
    assistant_response: str,
    max_messages: int = 10,
):
    """
    Maintain only the latest conversation turns.
    """

    updated = list(recent_messages)

    updated.extend(
        [
            {
                "role": "user",
                "content": user_query,
            },
            {
                "role": "assistant",
                "content": assistant_response[:1000],
            },
        ]
    )

    return updated[-max_messages:]


# ==========================================================
# Conversation Memory
# ==========================================================

def update_conversation_memory(
    state: GraphState,
    user_query: str,
    assistant_response: str,
) -> dict:
    """
    Update memory after a conversational response.

    No LLM summarization is performed.
    """

    conversation_turns = (
        state.get("conversation_turns", 0) + 1
    )

    recent_messages = update_recent_messages(
        state.get("recent_messages", []),
        user_query,
        assistant_response,
    )

    return {
        "recent_messages": recent_messages,
        "conversation_turns": conversation_turns,
    }


# ==========================================================
# Analysis Memory
# ==========================================================

def update_analysis_memory(
    state: GraphState,
    report: str,
) -> dict:
    """
    Update long-term memory after a completed analysis.
    """

    user_query = state["user_query"]

    execution_output = state.get(
        "execution_output",
        "",
    )

    chart_files = state.get(
        "chart_files",
        [],
    )

    new_summary = generate_memory_summary(
        user_query=user_query,
        execution_output=execution_output,
        report=report,
        chart_files=chart_files,
    )

    session_summary = state.get(
        "session_summary",
        "",
    )

    if session_summary and new_summary:

        session_summary += "\n\n" + new_summary

    elif new_summary:

        session_summary = new_summary

    conversation_turns = (
        state.get("conversation_turns", 0) + 1
    )

    if (
        conversation_turns % 5 == 0
        and session_summary
    ):

        session_summary = compress_memory(
            session_summary
        )

    recent_messages = update_recent_messages(
        state.get("recent_messages", []),
        user_query,
        report,
    )

    return {
        "session_summary": session_summary,
        "recent_messages": recent_messages,
        "conversation_turns": conversation_turns,
    }