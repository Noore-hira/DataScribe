import os
from src.config import llm
from src.graph.state import GraphState
from langchain_core.messages import SystemMessage, HumanMessage

def reporter_node(state: GraphState):
    """Compiles the final markdown report and automatically embeds any charts found in the 'charts' folder."""
    print("📝 Reporter is formatting the final output and checking for charts...")
    
    # Automatically scan the 'charts' directory for generated files
    charts_dir = "charts"
    embedded_charts_md = ""
    if os.path.exists(charts_dir):
        chart_files = os.listdir(charts_dir)
        if chart_files:
            print(f"📊 Found {len(chart_files)} chart(s) in 'charts/' folder. Embedding into report...")
            embedded_charts_md = "\n\n### Generated Visualizations & Interactive Dashboards\n"
            for file in chart_files:
                file_path = f"{charts_dir}/{file}"
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
        f"User Query: {state['user_query']}\n\n"
        f"Analysis & Execution Output:\n{state.get('execution_output', '')}\n\n"
        f"Dataset Schema:\n{state['df_schema']}"
    )
    
    response = llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_content)
    ])
    
    final_markdown = response.content + embedded_charts_md
    
    return {
        "final_report": final_markdown
    }