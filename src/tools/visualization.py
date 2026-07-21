import os
import re
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.tools import tool
from data_frame import global_df
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import llm_for_pg

matplotlib.use('Agg')
plt.style.use('dark_background')

@tool
def create_visualization_tool(plot_description: str) -> str:
    """
    Use this tool ONLY when you need to generate a chart, graph, or plot.
    Pass a highly detailed string describing the plot you want, including which columns to use for X and Y axes, 
    colors, and the title.
    """
    global global_df
    print(f"🎨 [VISUALIZER] Generating interactive Plotly/Seaborn plots: {plot_description}...")

    charts_dir = "charts"
    os.makedirs(charts_dir, exist_ok=True)

    sys_prompt = (
        "You are an expert Data Visualizer specializing in Plotly Express, Plotly Graph Objects, and Seaborn. "
        "Write clean, error-free Python code to generate gorgeous, interactive plots based on the user's request. "
        "CRITICAL ABSOLUTE RULES: "
        "1. The data is ALREADY loaded in memory as a pandas DataFrame named `global_df`. DO NOT read files. "
        "2. PREFER PLOTLY (`px` or `go`) for interactive charts (donuts, scatter, 3D, bar, animated plots). "
        "3. DARK THEME ENFORCEMENT: "
        "   - For Plotly, always add `template='plotly_dark'` and `fig.update_layout(paper_bgcolor='black', plot_bgcolor='black')`. "
        "   - For colorscales, use valid built-in strings like 'Viridis', 'Plasma', 'Blues', 'Greens', 'Turbo'. NEVER pass custom tuples or invalid strings like 'Plotly' to colorways. "
        "4. SAVING FILES: "
        "   - Save Plotly figures as interactive HTML files: `fig.write_html('charts/filename.html')`. "
        "   - Save Matplotlib/Seaborn as PNGs: `plt.savefig('charts/filename.png', bbox_inches='tight', facecolor='black')`. "
        "   - DO NOT use `plt.show()` or `fig.show()`. "
        "5. IF MULTIPLE PLOTS ARE REQUESTED, write the code to generate and save ALL of them in this single script. "
        "6. OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks."
    )
    
    user_prompt = f"Data Columns Available: {list(global_df.columns)}\nData Schema:\n{global_df.dtypes}\n\nPlot Request: {plot_description}"
    
    response = llm_for_pg.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    raw_output = response.content
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else raw_output
    
    # SAFETY INTERCEPT: Scrub accidental file reads
    if "read_csv" in code or "pd.read" in code:
        print("⚠️ [VISUALIZER WARNING] LLM attempted to read a file. Scrubbing...")
        code_lines = [line for line in code.split("\n") if "read_csv" not in line and "pd.read" not in line]
        code = "\n".join(code_lines)

    # SMART PATH SANITIZER: Ensure files are saved in 'charts/' without duplication
    def sanitize_path(match):
        full_call = match.group(0)
        filename = os.path.basename(match.group(2))
        return full_call.replace(match.group(2), f"charts/{filename}")

    code = re.sub(r"(plt\.savefig|fig\.write_html)\s*\(\s*(['\"])(.*?)\1", sanitize_path, code)

    exec_globals = {
        "global_df": global_df,
        "plt": plt,
        "sns": sns,
        "px": px,
        "go": go
    }
    
    try:
        exec(code, exec_globals)
        saved_files = os.listdir(charts_dir)
        msg = f"SUCCESS: Interactive plots successfully saved in 'charts/'. Generated files: {', '.join(saved_files)}"
        print(f"✅ [VISUALIZER SUCCESS] Plots saved in 'charts/' -> {saved_files}")
        return msg
    except Exception as e:
        error_msg = str(e)
        print(f"❌ [VISUALIZER CRASHED] The generated code failed: {error_msg}")
        return f"FAILED to generate plot due to code error: {error_msg}."