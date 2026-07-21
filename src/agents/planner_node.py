import re

from src.config import llm_for_pg
from src.graph.state import GraphState

def planner_node(state: GraphState):
    """The Planner reads the user query and schema, writing a text roadmap."""
    print("Planner is creating a step-by-step roadmap...")
    
    prompt = (
        f"User Query: {state['user_query']}\n"
        f"Dataset Schema:\n{state['df_schema']}\n\n"
        "Write a concise, high-level execution plan to satisfy this query. "
        "Specify the required analysis, charts, and statistical calculations.\n\n"
        "PLANNER BOUNDARY: Return a roadmap only. Do not write Python, pseudocode, "
        "imports, library calls, code snippets, file paths, or implementation examples. "
        "The dataset is already loaded by the workflow; do not instruct the next stage "
        "to load it. The programmer and designer nodes handle implementation."
    )
    
    try:
        response = llm_for_pg.invoke(prompt)
    except Exception as exc:
        message = f"The planning model is unavailable: {exc.__class__.__name__}. Please retry after the model service is available."
        return {"fatal_error": message, "final_report": message}
    # Keep the planner/programmer boundary intact if the model disregards the
    # prompt and appends a fenced implementation example.
    plan = re.sub(r"```(?:python)?\s*.*?```", "", response.content, flags=re.DOTALL).strip()
    return {"plan": plan}
