from src.config import llm_for_pg
from src.graph.state import GraphState

def planner_node(state: GraphState):
    """The Planner reads the user query and schema, writing a text roadmap."""
    print("📋 Planner is creating a step-by-step roadmap...")
    
    prompt = (
        f"User Query: {state['user_query']}\n"
        f"Dataset Schema:\n{state['df_schema']}\n\n"
        "Write a clean, high-level step-by-step execution plan to satisfy this query. "
        "Specify if charts/plots are needed and what statistical calculations are required."
    )
    
    response = llm_for_pg.invoke(prompt)
    return {"plan": response.content}