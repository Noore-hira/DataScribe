from typing import Annotated, Any
from pydantic import BaseModel

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Optional

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    df_schema: Optional[str]
    memory_usage_mb: Optional[float]
    plan: Optional[str]
    current_code: Optional[str]
    execution_output: Optional[str]
    has_error: Optional[bool]
    retry_count: Optional[int]
    revision_count: Optional[int]
    supervisor_decision: Optional[str]
    charts_completed: Optional[bool]
    final_report: Optional[str]  # Final generated markdown report[cite: 7]