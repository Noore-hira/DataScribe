import re
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.tools import tool
from data_frame import global_df
from langchain_core.messages import SystemMessage, HumanMessage

# Force matplotlib to not open pop-up windows on the server
matplotlib.use('Agg')
# Force Matplotlib and Seaborn to use a black background by default
plt.style.use('dark_background')

# Import your LLM from config
from src.config import llm_for_pg

@tool
def create_visualization_tool(plot_description: str) -> str:
    """
    Use this tool ONLY when you need to generate a chart, graph, or plot.
    Pass a highly detailed string describing the plot you want, including which columns to use for X and Y axes, 
    colors, and the title.
    """
    global global_df
    print(f"🎨 [VISUALIZER] Generating plot: {plot_description}...")

    # 1. Prompt the specific Visualizer LLM with strict dark mode rules
    sys_prompt = (
        "You are an expert Data Visualizer. Write Python code to generate beautiful, "
        "publication-ready plots based on the user's request. "
        "CRITICAL RULES: "
        "1. The data is available in a pandas DataFrame named `global_df`. "
        "2. Use `seaborn`, `matplotlib.pyplot`, or `plotly.express`. "
        "3. THE BACKGROUND MUST BE BLACK. "
        "   - If using Plotly, add `template='plotly_dark'` and `fig.update_layout(paper_bgcolor='black', plot_bgcolor='black')`. "
        "   - If using Matplotlib/Seaborn, dark_background is active. "
        "4. CREATE UNIQUE FILENAMES: Save each plot with a descriptive filename based on what it shows "
        "   (e.g., `plt.savefig('sales_by_region_bar.png', bbox_inches='tight', facecolor='black')`). DO NOT use `output_plot.png`. DO NOT use `plt.show()`. "
        "5. If using plotly, save it dynamically as well (e.g., `fig.write_html('salary_distribution.html')`). DO NOT use `fig.show()`. "
        "6. IF THE USER ASKS FOR MULTIPLE PLOTS, write the code to generate and save ALL of them using distinct filenames. "
        "7. If the user asks for charts, YOU MUST CALL the `create_visualization_tool` EXACTLY ONCE.\n"
        "8. If multiple charts are requested, COMBINE them into a single string for that ONE tool call."
        "9. OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks."
    )
    
    # We pass the schema so the visualizer knows exactly what columns exist
    user_prompt = f"Data Schema:\n{global_df.dtypes}\n\nPlot Request: {plot_description}"
    
    response = llm_for_pg.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    # 2. Extract the Python code
    raw_output = response.content
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else raw_output
    
    # 3. Execute in an isolated sandbox
    exec_globals = {
        "global_df": global_df,
        "plt": plt,
        "sns": sns,
        "px": px,
        "go": go
    }
    
    try:
        exec(code, exec_globals)
        msg = "SUCCESS: The plots were successfully saved. Proceed to Step 2."
        print(f"✅ [VISUALIZER SUCCESS] Plots saved!")
        return msg
    except Exception as e:
        error_msg = str(e)
        # 1. Print the error to your terminal so you can debug it
        print(f"❌ [VISUALIZER CRASHED] The generated code failed: {error_msg}")
        
        # 2. Force the Programmer to STOP retrying
        return (
            f"FAILED to generate plot due to this code error: {error_msg}. "
            "CRITICAL INSTRUCTION: DO NOT CALL THIS TOOL AGAIN. Accept the failure "
            "and immediately proceed to Step 2 to write the Pandas analysis code."
        )