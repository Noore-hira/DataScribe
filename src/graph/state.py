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

    messages: Annotated[list, add_messages]
    user_query: str

    # =====================================================
    # Dataset
    # =====================================================

    df_schema: str
    memory_usage_mb: float

    # =====================================================
    # Planning
    # =====================================================

    plan: str

    # =====================================================
    # Supervisor
    # =====================================================
    supervisor_decision: Literal[ "planner","reporter","end" ]
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