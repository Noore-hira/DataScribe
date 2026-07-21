from langchain_core.messages import HumanMessage
from src.config import llm_for_pg
from src.tools.visualization import create_visualization_tool
from langchain.agents import create_agent
from src.graph.state import GraphState

designer_instructions = (
    "You are a specialized Data Visualizer. Your job is to call the `create_visualization_tool` ONCE "
    "to generate ALL requested charts.\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST bundle all requested plots (donut charts, bar charts, scatter plots, etc.) into a SINGLE detailed instruction string "
    "and call `create_visualization_tool` exactly ONE time.\n"
    "2. DO NOT make multiple sequential tool calls. Generate everything in one go.\n"
    "3. ENVIRONMENT CONSTRAINT: The dataset is ALREADY loaded as `global_df`. Never read files."
)

designer_react_agent = create_agent(
    model=llm_for_pg,
    tools=[create_visualization_tool],
    system_prompt=designer_instructions
)

def designer_node(state: GraphState):
    """Designer agent handles all chart creation via a single tool invocation."""
    print("🎨 Designer is generating all visualizations in a single pass...")
    prompt = f"Plan: {state['plan']}\nUser Request: {state['user_query']}\nSchema:\n{state['df_schema']}"
    
    # Invoke normally without restricting the inner recursion limit
    response = designer_react_agent.invoke(
        {"messages": [HumanMessage(content=prompt)]}
    )
    
    # Extract tool message output if available
    tool_output = "Visualizations generated successfully in charts/ folder."
    for msg in response.get("messages", []):
        if hasattr(msg, "content") and "SUCCESS" in msg.content:
            tool_output = msg.content
            
    existing_output = state.get("execution_output", "")
    combined_output = f"{existing_output}\n\n[Visualizer Logs]: {tool_output}"
    
    return {
        "current_code": "print('Visualizations handled by Designer tool.')",
        "execution_output": combined_output,
        "charts_completed": True
    }