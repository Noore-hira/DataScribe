import re
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent  # <-- Using the correct v1 standard

from src.config import llm_for_pg
from src.tools.data_cleaning import clean_dataframe_tool
from src.tools.visualization import create_visualization_tool
from src.graph.state import GraphState

# --- FIX 1: The "Order of Operations" Prompt ---
programmer_instructions = (
    "You are an expert Data Engineer. You have access to a data visualization tool.\n\n"
    "CRITICAL ORDER OF OPERATIONS:\n"
    "STEP 1: VISUALIZATIONS (If requested)\n"
    "- If the user asks for charts, YOU MUST CALL the `create_visualization_tool` EXACTLY ONCE.\n"
    "- If multiple charts are requested, COMBINE them into a single string for that ONE tool call (e.g., 'Generate a bar chart of X, AND a pie chart of Y'). DO NOT call the tool multiple times.\n"
    "- Do NOT write any matplotlib code yourself.\n\n"
    "STEP 2: DATA ANALYSIS (Required)\n"
    "- Write the Pandas Python code to analyze `global_df`.\n"
    "- You MUST use `print()` statements (e.g., `print(global_df.describe())`) so the Reporter gets the numbers.\n"
    "- Wrap your final Pandas code inside ```python ... ``` blocks."
)

# Create the autonomous agent using the LangChain v1 function
programmer_react_agent = create_agent(
    model=llm_for_pg,  # <-- In v1, the parameter is strictly named 'model'
    tools=[clean_dataframe_tool, create_visualization_tool],
    system_prompt=programmer_instructions
)

def programmer_node(state: GraphState):
    """Invokes the Programmer Agent to handle optional tool use and code generation."""
    print("💻 Programmer Agent is reasoning and writing code...")
    
    # 1. Check for persistent tool failure count
    tool_retry_count = state.get("tool_retry_count", 0)
    
    # 2. Construct context with "Give up" circuit breaker
    tool_context = ""
    if tool_retry_count >= 5:
        tool_context = "\n\nCRITICAL: You have failed to use the visualization tool 5 times. ABANDON ALL PLOTS. Move directly to Step 2 and write Pandas math code."
    
    error_context = ""
    if state.get("has_error"):
        error_context = f"\n\nYOUR PREVIOUS CODE FAILED:\n{state['execution_output']}\nFix it."
    elif state.get("supervisor_decision") == "rework":
        error_context = f"\n\nSUPERVISOR REJECTED PREVIOUS REPORT:\n{state['plan']}\nRewrite the logic."

    user_message = f"Plan: {state['plan']}\nSchema:\n{state['df_schema']}{error_context}{tool_context}"
    
    # 3. Invoke with history
    messages_to_send = state.get("messages", []) + [HumanMessage(content=user_message)]
    
    response = programmer_react_agent.invoke({
        "messages": messages_to_send
    })
    
    raw_output = response["messages"][-1].content
    
    # 4. Extract Code
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else "print('Agent executed a tool or provided text. No Pandas math block generated.')"
    
    # 5. Calculate new retry counts
    # If the LLM output says FAILED, increment our visualization retry counter
    is_tool_failed = "FAILED" in raw_output
    new_tool_retry_count = tool_retry_count + 1 if is_tool_failed else 0
    
    new_retry_count = state.get("retry_count", 0) + 1 if state.get("has_error") else 0
        
    return {
        "current_code": code, 
        "retry_count": new_retry_count,
        "tool_retry_count": new_tool_retry_count
    }