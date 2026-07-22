from typing import Annotated, Literal
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, NotRequired


class InputState(TypedDict):
    """The only value an end user needs to provide in LangGraph Studio."""

    user_query: str


class GraphState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    user_query: str
    df_schema: NotRequired[str]
    memory_usage_mb: NotRequired[float]
    plan: NotRequired[str]
    critic_verdict: NotRequired[Literal["pass", "fail"]]
    critic_feedback: NotRequired[str]
    current_code: NotRequired[str]
    execution_output: NotRequired[str]
    has_error: NotRequired[bool]
    retry_count: NotRequired[int]
    revision_count: NotRequired[int]
    supervisor_decision: NotRequired[str]
    charts_completed: NotRequired[bool]
    chart_files: NotRequired[list[str]]
    fatal_error: NotRequired[str]
    final_report: NotRequired[str]
