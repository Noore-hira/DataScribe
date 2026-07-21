from src.graph.state import GraphState
from data_frame import load_dataframe
import io

def supervisor_node(state: GraphState):
    """Route deterministically to avoid expensive, non-deterministic LLM routing."""
    print("Supervisor is evaluating workflow state...")

    df_schema = state.get("df_schema", "")
    if not df_schema:
        print("Auto-generating dataset schema for incoming run...")
        buffer = io.StringIO()
        dataframe = load_dataframe()
        dataframe.info(buf=buffer)
        df_schema = buffer.getvalue()

    if state.get("fatal_error") or state.get("final_report"):
        decision = "end"
    elif not state.get("plan"):
        decision = "planner"
    elif not state.get("execution_output"):
        decision = "programmer"
    elif _needs_charts(state.get("user_query", "")) and not state.get("charts_completed"):
        decision = "designer"
    else:
        decision = "reporter"

    print(f"Supervisor routing decision -> {decision.upper()}")
    return {"df_schema": df_schema, "supervisor_decision": decision}


def _needs_charts(user_query: str) -> bool:
    return any(keyword in user_query.lower() for keyword in ("chart", "plot", "donut", "bar", "graph", "visual"))
