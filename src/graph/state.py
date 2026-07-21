from typing import Annotated, Any
from pydantic import BaseModel

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Optional

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    df_schema: str
    memory_usage_mb: float       # NEW: Triggers Polars if > 2000
    supervisor_decision: str     # NEW: State tracker for routing
    plan: str
    revision_count: int  # NEW: Tracks how many times the Supervisor rejects the report
    current_code: str
    execution_output: str
    has_error: bool
    retry_count: int
    tool_retry_count: int
    final_report: Optional[str]