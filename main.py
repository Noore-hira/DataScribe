import sys
import io
import re
import os
import base64
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # NEW
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

load_dotenv()
api_key=os.getenv("GROQ_API")

def encode_image(image_path):
    """Encodes an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
# ==========================================
# 1. DEFINE THE STATE (No changes)
# ==========================================
class GraphState(TypedDict):
    user_query: str
    df_schema: str
    plan: str
    current_code: str
    execution_output: str
    has_error: bool
    retry_count: int
    final_report: str

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, api_key=api_key)
llm_vision = ChatGroq(model="qwen/qwen3.6-27b", temperature=0.1, api_key=api_key)
# ==========================================
# 2. DEFINE THE AGENT NODES (Updated Prompts & Logic)
# ==========================================

def supervisor_node(state: GraphState):
    sys_prompt = (
        "You are a Senior Data Scientist managing a project. "
        "Review the user's query and the Pandas DataFrame schema. "
        "Write a brief, precise step-by-step plan on how to write Python/Pandas "
        "code to extract the necessary insights. Assume the dataframe is loaded as `df`."
    )
    
    user_content = f"Query: {state['user_query']}\n\nSchema:\n{state['df_schema']}"
    
    response = llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_content)
    ])
    print("------ SUPERVISOR NODE ------")
    return {"plan": response.content}

def programmer_node(state: GraphState):
    """Writes the actual Pandas code based on the plan and past errors."""
    print("------ PROGRAMMER NODE ------")
    # --- UPDATED: Instructions for BEAUTIFUL VISUALIZATIONS ---
    visualization_instr = (
        "\n\n*** VISUALIZATION INSTRUCTIONS ***\n"
        "If the user asks for a chart or graph, follow these aesthetic rules:\n"
        "1.  Use the **Seaborn** library (`sns`) for all plots. Do NOT use standard Matplotlib (`plt`) commands for drawing.\n"
        "2.  Always call `sns.set_theme(style='whitegrid', palette='muted')` first.\n"
        "3.  Use appropriate chart types (e.g., `sns.barplot`, `sns.scatterplot`, `sns.histplot`).\n"
        "4.  Maximize the Data-Ink Ratio: Keep charts clean and minimalist.\n"
        "5.  Ensure all charts have clear, descriptive titles (`plt.title()`), x-labels (`plt.xlabel()`), and y-labels (`plt.ylabel()`).\n"
        "6.  Increase font sizes slightly for readability: `plt.rcParams.update({'font.size': 14})`\n"
        "7.  **Do NOT use `plt.show()`**. It will cause the script to block.\n"
        "8.  You must save the plot to the local directory as `agent_chart.png` using `plt.savefig('agent_chart.png', bbox_inches='tight', dpi=150)`.\n"
        "9.  Always clear the figure afterward with `plt.clf()`."
    )

    sys_prompt = (
        "You are an expert Python Pandas developer specializing in beautiful visualizations. "
        "Write code based on the provided plan. The dataframe is already loaded as a variable named `df`. "
        "The following libraries are imported and ready: `pd`, `plt`, `sns`. "
        "Print the final results using standard print() statements so they can be captured. "
        "OUTPUT ONLY PYTHON CODE inside ```python ... ``` blocks. Do not add explanations."
        f"{visualization_instr}"
    )
    
    error_context = ""
    if state.get("has_error") and state.get("execution_output"):
        error_context = f"\n\nYOUR PREVIOUS CODE FAILED WITH THIS ERROR:\n{state['execution_output']}\nFix the code."

    user_content = f"Plan: {state['plan']}\n\nSchema:\n{state['df_schema']}{error_context}"
    
    response = llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_content)
    ])
    
    raw_output = response.content
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else raw_output
    
    new_retry_count = state.get("retry_count", 0)
    if state.get("has_error"):
        new_retry_count += 1
        
    return {"current_code": code, "retry_count": new_retry_count}

def executor_node(state: GraphState):
    """Pure Python execution tool. NO LLM logic here."""
    print("------ EXECUTOR NODE ------")
    code = state["current_code"]
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    error_msg = None
    
    # --- UPDATED: We inject `sns` and `plt` along with `df` ---
    # Set high-DPI backend for better static images
    plt.switch_backend('Agg') 
    
    # We assume 'df' was fixed from your previous issue (e.g., Option A or B)
    # Using 'globals().get("df")' handles a global definition of 'df'.
    # If you renamed it to 'global_df', replace it here.
    df_instance = globals().get("df")
    
    exec_globals = {
        "df": df_instance,
        "plt": plt,
        "sns": sns  # NEW
    }
    
    try:
        exec(code, exec_globals)
    except Exception as e:
        error_msg = str(e)
    finally:
        sys.stdout = old_stdout
        
    if error_msg:
        return {"execution_output": error_msg, "has_error": True}
    else:
        return {"execution_output": redirected_output.getvalue(), "has_error": False}

def critic_node(state: GraphState):
    print("------ CRITIC NODE ------")
    return {"has_error": state["has_error"]}

def reporter_node(state: GraphState):
    print("------ REPORTER NODE ------")
    sys_prompt = (
        "You are an expert Data Analyst. Describe the visual trends in the provided chart."
    )
    
    text_content = f"Original Query: {state['user_query']}\nRaw Output:\n{state['execution_output']}"
    content_payload = [{"type": "text", "text": text_content}]
    
    chart_path = "agent_chart.png"
    if os.path.exists(chart_path):
        base64_image = encode_image(chart_path)
        content_payload.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        })
    
    # Notice we are invoking llm_vision here, NOT the standard llm
    response = llm_vision.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=content_payload)
    ])
    
    return {"final_report": response.content}
# ==========================================
# 3. DEFINE ROUTING LOGIC & COMPILE GRAPH (No changes)
# ==========================================

def route_after_execution(state: GraphState):
    if state["has_error"] and state["retry_count"] < 3:
        print(f"Code execution failed. Retrying... (Attempt {state['retry_count'] + 1})")
        return "programmer"
    elif state["has_error"]:
        print("Max retries hit. Proceeding to report with error.")
        return "reporter"
    else:
        print("Code executed successfully.")
        return "reporter"

workflow = StateGraph(GraphState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

workflow.set_entry_point("supervisor")
workflow.add_edge("supervisor", "programmer")
workflow.add_edge("programmer", "executor")
workflow.add_edge("executor", "critic")

workflow.add_conditional_edges(
    "critic",
    route_after_execution,
    {
        "programmer": "programmer",
        "reporter": "reporter"
    }
)

workflow.add_edge("reporter", END)
app = workflow.compile()

# ==========================================
# 4. RUN THE PIPELINE (Updated for visualization check)
# ==========================================
if __name__ == "__main__":
    import os

    data = {
        "Department": ["Sales", "Engineering", "Sales", "HR", "Engineering", "Sales", "HR", "Engineering", "HR"],
        "Employee": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Heidi", "Ivan"],
        "Salary": [85000, 120000, 90000, 70000, 125000, 95000, 72000, 130000, 68000],
        "Satisfaction": [8, 9, 6, 9, 8, 7, 10, 8, 7]
    }
    
    # DEFINE 'df' GLOBALLY so executor can find it
    df = pd.DataFrame(data)
    
    # 2. Extract schema text dynamically
    buffer = io.StringIO()
    df.info(buf=buffer)
    schema_str = buffer.getvalue() + f"\n\nSample Data:\n{df.head(3).to_markdown()}"

    # 3. Define the query requesting a visual result
    initial_state = {
        "user_query": "Create a beautiful donut chart showing every employee with their salaries and also summarize the key insights",
        "df_schema": schema_str,
        "retry_count": 0,
        "has_error": False
    }

    print("Starting agentic workflow (visualization focus)...")
    result = app.invoke(initial_state)
    
    print("\n" + "="*40)
    print("FINAL REPORT")
    print("="*40)
    # Use regex to remove everything inside <think> tags (including the tags themselves)
    clean_report = re.sub(r'<think>.*?</think>', '', result["final_report"], flags=re.DOTALL).strip()

    print(clean_report)
    
    # CHECK FOR CHART OUTPUT
    chart_path = "agent_chart.png"
    if os.path.exists(chart_path):
        print(f"\nChart saved successfully to directory: {chart_path}")
    else:
        print("\nAgent failed to generate a chart.")
