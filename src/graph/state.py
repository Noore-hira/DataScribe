from typing import Annotated, Literal

from typing_extensions import NotRequired, TypedDict

from langgraph.graph.message import add_messages


class GraphState(TypedDict, total=False):
    """
    Shared state across all LangGraph nodes.
    """

    # =====================================================
    # Conversation
    # =====================================================

    # LangGraph message history
    messages: Annotated[list, add_messages]

    # Current user query
    user_query: str

    # Route chosen by Conversation Agent
    conversation_route: Literal[
        "answer",
        "workflow",
        "reject",
    ]

    # =====================================================
    # Conversation Memory
    # =====================================================

    # Running summary of the conversation
    session_summary: str

    # Last few user/assistant exchanges
    recent_messages: list

    # Number of completed conversation turns
    conversation_turns: int

    # =====================================================
    # Dataset
    # =====================================================

    df_schema: str
    memory_usage_mb: float

    # Dataset metadata remembered across the session
    dataset_name: NotRequired[str]
    dataset_summary: NotRequired[str]

    # =====================================================
    # Planning
    # =====================================================

    plan: str

    # =====================================================
    # Supervisor
    # =====================================================

    supervisor_decision: Literal[
        "planner",
        "reporter",
        "end",
    ]

    supervisor_feedback: NotRequired[str]

    supervisor_review_count: NotRequired[int]

    max_supervisor_reviews: NotRequired[int]

    # =====================================================
    # Programmer
    # =====================================================

    generated_code: NotRequired[str]

    agent_output: NotRequired[str]

    # =====================================================
    # Execution
    # =====================================================

    execution_status: NotRequired[
        Literal[
            "success",
            "failed",
        ]
    ]

    execution_output: NotRequired[str]

    execution_error: NotRequired[str]

    chart_files: NotRequired[list[str]]

    # =====================================================
    # Retry
    # =====================================================

    retry_count: NotRequired[int]

    max_retries: NotRequired[int]

    # =====================================================
    # Critic
    # =====================================================

    critic_verdict: NotRequired[
        Literal[
            "pass",
            "fail",
            "abort",
        ]
    ]

    critic_feedback: NotRequired[str]

    # =====================================================
    # Fatal Error
    # =====================================================

    fatal_error: NotRequired[str]

    # =====================================================
    # Final Report
    # =====================================================

    final_report: NotRequired[str]