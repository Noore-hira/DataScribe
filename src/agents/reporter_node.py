import os
from src.config import llm
from src.graph.state import GraphState
from src.logs.logger import logger
from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state_utils import require_state

def reporter_node(state: GraphState):
    """Compile the final report with only artifacts created by this graph run."""
    logger.info("Reporter is formatting the final output and checking for charts...")
    
    if state.get("fatal_error"):
        return {"final_report": state["fatal_error"]}
    
    # Use the explicit artifact list for this run. Do not include stale files
    # created by earlier Studio threads.
    embedded_charts_md = ""
    chart_files = state.get("chart_files", [])
    if chart_files:
        print(f"Found {len(chart_files)} chart(s) for this run. Embedding into report...")
        embedded_charts_md = "\n\n### Generated Visualizations & Interactive Dashboards\n"
        for file_path in chart_files:
            file = os.path.basename(file_path)
            if file.endswith(".html"):
                # Embed interactive Plotly charts via iframe
                embedded_charts_md += f"\n- **{file}**:\n  <iframe src='{file_path}' width='100%' height='500px' style='border:none;'></iframe>\n"
            elif file.endswith(".png"):
                # Embed static matplotlib/seaborn charts via markdown image
                embedded_charts_md += f"\n- **{file}**:\n  ![{file}]({file_path})\n"

    sys_prompt = (
            "You are an expert Data Science Technical Writer. Your job is to compile a professional, "
            "comprehensive final markdown report based on the provided data cleaning execution outputs, "
            "summary statistics, and insights.\n"
            "CRITICAL RULE: Do NOT write Python code blocks or code examples for the charts or visualizations. "
            "The charts have already been automatically generated and embedded as interactive dashboards at the end of the report. "
            "Focus purely on presenting data insights, tables, statistics, and business findings."
        )
    
    user_content = (
        f"User Query: {require_state(state, "user_query")}\n\n"
        f"Analysis & Execution Output:\n{state.get('execution_output', '')}\n\n"
        f"Dataset Schema:\n{require_state(state, "df_schema")}"
    )
    
    try:
        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_content)
        ])
    except Exception as exc:
        return {"final_report": f"Analysis completed, but the reporting model is unavailable ({exc.__class__.__name__}).\n\nRaw results:\n{state.get('execution_output', '')}" + embedded_charts_md}
    
    final_markdown = response.content + embedded_charts_md
    
    return {
        "final_report": final_markdown
    }
