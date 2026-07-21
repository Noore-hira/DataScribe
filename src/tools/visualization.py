import os
import re
import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.tools import tool
from data_frame import load_dataframe
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import llm_for_pg
from src.tools.safe_execution import SAFE_BUILTINS, normalize_visualization_artifacts, validate_analysis_code

matplotlib.use('Agg')
plt.style.use('dark_background')

@tool
def create_visualization_tool(plot_description: str, run_id: str) -> str:
    """
    Use this tool ONLY when you need to generate a chart, graph, or plot.
    Pass a highly detailed string describing the plot you want, including which columns to use for X and Y axes, 
    colors, and the title.
    """
    print(f"[VISUALIZER] Generating interactive Plotly/Seaborn plots: {plot_description}...")

    charts_dir = os.path.join("charts", run_id)
    os.makedirs(charts_dir, exist_ok=True)
    global_df = load_dataframe()

    sys_prompt = (
        "You are an expert Data Visualizer specializing in Plotly Express, Plotly Graph Objects, and Seaborn. "
        "Write clean, error-free Python code to generate gorgeous, interactive plots based on the user's request. "
        "CRITICAL ABSOLUTE RULES: "
        "1. The data is ALREADY loaded in memory as a pandas DataFrame named `global_df`. DO NOT read files. "
        "1a. Do not use import statements; `px`, `go`, `sns`, and `plt` are already available. "
        "2. PREFER PLOTLY (`px` or `go`) for interactive charts (donuts, scatter, 3D, bar, animated plots). "
        "3. DARK THEME ENFORCEMENT: "
        "   - For Plotly, always add `template='plotly_dark'` and `fig.update_layout(paper_bgcolor='black', plot_bgcolor='black')`. "
        "   - For colorscales, use valid built-in strings like 'Viridis', 'Plasma', 'Blues', 'Greens', 'Turbo'. NEVER pass custom tuples or invalid strings like 'Plotly' to colorways. "
        "4. SAVING FILES: "
        f"   - Save Plotly figures as interactive HTML files inside `{charts_dir}/`, for example `fig.write_html('{charts_dir}/chart.html')`. "
        f"   - Save Matplotlib/Seaborn as PNGs inside `{charts_dir}/`, for example `plt.savefig('{charts_dir}/chart.png', bbox_inches='tight', facecolor='black')`. "
        "   - DO NOT use `plt.show()` or `fig.show()`. "
        "5. IF MULTIPLE PLOTS ARE REQUESTED, write the code to generate and save ALL of them in this single script. "
        "6. OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks."
    )
    
    user_prompt = f"Data Columns Available: {list(global_df.columns)}\nData Schema:\n{global_df.dtypes}\n\nPlot Request: {plot_description}"
    
    try:
        response = llm_for_pg.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ])
    except Exception as exc:
        return json.dumps({"status": "failed", "files": [], "error": f"Visualization model unavailable: {exc.__class__.__name__}"})
    
    raw_output = response.content
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else raw_output
    code = re.sub(r"^\s*(?:from\s+\S+\s+import\s+.+|import\s+.+)\s*$", "", code, flags=re.MULTILINE)
    code = re.sub(r"^\s*(?:plt|fig)\.show\(\)\s*$", "", code, flags=re.MULTILINE)

    code = normalize_visualization_artifacts(code, charts_dir)
    
    exec_globals = {
        "__builtins__": SAFE_BUILTINS,
        "global_df": global_df,
        "plt": plt,
        "sns": sns,
        "px": px,
        "go": go
    }
    
    try:
        exec(compile(validate_analysis_code(code, artifact_dir=charts_dir), "<generated-visualization>", "exec"), exec_globals)
        saved_files = [os.path.join(charts_dir, filename).replace("\\", "/") for filename in os.listdir(charts_dir)]
        if not saved_files:
            return json.dumps({"status": "failed", "files": [], "error": "The visualizer did not create any chart files."})
        msg = json.dumps({"status": "success", "files": saved_files})
        print(f"[VISUALIZER SUCCESS] Plots saved in 'charts/' -> {saved_files}")
        return msg
    except Exception as e:
        error_msg = str(e)
        print(f"[VISUALIZER CRASHED] The generated code failed: {error_msg}")
        return json.dumps({"status": "failed", "files": [], "error": error_msg})
