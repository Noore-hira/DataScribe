import io
import pandas as pd
from src.graph.state import GraphState
from data_frame import global_df
from langgraph.graph import StateGraph, END
from src.agents.executor_node import executor_node
from src.agents.supervisor_node import supervisor_node
from src.agents.critic_node import critic_node
from src.agents.profiler_node import profiler_node
from src.agents.reporter_node import reporter_node
from src.agents.programmer_node import programmer_node
from langgraph.checkpoint.memory import MemorySaver

# 1. Initialize the memory saver
memory = MemorySaver()

def route_from_supervisor(state: GraphState):
    decision = state["supervisor_decision"]
    if decision == "profile": return "profiler"
    elif decision in ["analyze", "rework"]: return "programmer"
    elif decision == "approve": return END

def route_from_critic(state: GraphState):
    if state["has_error"] and state["retry_count"] < 3: return "programmer"
    return "reporter"

workflow = StateGraph(GraphState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("profiler", profiler_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

workflow.set_entry_point("supervisor")

# Supervisor routing
workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {"profiler": "profiler", "programmer": "programmer", END: END}
)

# Execution loop
workflow.add_edge("programmer", "executor")
workflow.add_edge("executor", "critic")

workflow.add_conditional_edges(
    "critic",
    route_from_critic,
    {"programmer": "programmer", "reporter": "reporter"}
)

# New Cyclic Review: Reporter goes back to Supervisor for final approval
workflow.add_edge("reporter", "supervisor")
workflow.add_edge("profiler", "supervisor")

app = workflow.compile(checkpointer=memory)

png_bytes = app.get_graph().draw_mermaid_png()
with open("workflow_diagram.png", "wb") as f:
    f.write(png_bytes)
print("📸 Workflow diagram saved as 'workflow_diagram.png'")

# In main_graph.py or your API route:
user_thread_id = "user_session_123" # This comes from your database/session ID

config = {"configurable": {"thread_id": user_thread_id}}

if __name__ == "__main__":
    # Calculate Memory Footprint (Forced to standard float)
    mem_usage_bytes = global_df.memory_usage(deep=True).sum()
    mem_usage_mb = float(mem_usage_bytes / (1024 ** 2)) # <-- FIX IS HERE
    
    buffer = io.StringIO()
    global_df.info(buf=buffer)
    schema_str = f"{buffer.getvalue()}\n\nNull Count:\n{global_df.isnull().sum()}"

    initial_state = {
        "user_query": "tell me about the dataset and give me insights from it and also create donut plot and bar chart and other which are suitable",
        "df_schema": schema_str,
        "memory_usage_mb": mem_usage_mb, # This is now a safe Python float!
        "retry_count": 0,
        "revision_count": 0,
        "has_error": False,
        "final_report": None
    }

    print("🚀 Starting Production Agentic Workflow...\n")
    result = app.invoke(initial_state, config=config)
    
    print("\n" + "="*40)
    print("✅ FINAL APPROVED REPORT")
    print("="*40)

    # Failsafe in case the graph terminates early without a report
    if result.get("final_report"):
        print(result["final_report"])
    else:
        print("Graph execution completed, but no final report was generated.")