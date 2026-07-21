import json
from uuid import uuid4

from src.tools.visualization import create_visualization_tool
from src.graph.state import GraphState

def designer_node(state: GraphState):
    """Generate all requested charts in one call and retain only this run's files."""
    print("Designer is generating all visualizations in a single pass...")
    prompt = f"Plan: {state['plan']}\nUser Request: {state['user_query']}\nSchema:\n{state['df_schema']}"
    run_id = f"run_{uuid4().hex}"
    tool_output = create_visualization_tool.invoke({"plot_description": prompt, "run_id": run_id})
    try:
        result = json.loads(tool_output)
    except json.JSONDecodeError:
        result = {"status": "failed", "files": [], "error": "Visualizer returned an invalid response."}

    existing_output = state.get("execution_output", "")
    combined_output = f"{existing_output}\n\n[Visualizer Logs]: {result}"
    if result.get("status") != "success":
        return {"execution_output": combined_output, "charts_completed": False, "fatal_error": f"Visualization failed: {result.get('error', 'unknown error')}", "final_report": f"Visualization failed: {result.get('error', 'unknown error')}"}

    return {
        "execution_output": combined_output,
        "charts_completed": True,
        "chart_files": result["files"]
    }
