from src.graph.state import GraphState

def critic_node(state: GraphState):
    """Checks for standard python errors."""
    print("------ CRITIC NODE ------")
    return {"has_error": state["has_error"]}