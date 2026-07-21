import io
import os
from dotenv import load_dotenv
import pandas as pd
from src.graph.state import GraphState
from data_frame import global_df
from langgraph.graph import StateGraph, END
from src.agents.executor_node import executor_node
from src.agents.supervisor_node import supervisor_node
from src.agents.critic_node import critic_node
from src.agents.planner_node import planner_node
from src.agents.designer_node import designer_node
from src.agents.reporter_node import reporter_node
from src.agents.programmer_node import programmer_node
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_TRACING_V2"]=os.getenv("LANGSMITH_TRACING_V2")
os.environ["LANGSMITH_PROJECT"]=os.getenv("LANGSMITH_PROJECT")
memory = MemorySaver()

def route_from_supervisor(state: GraphState):
    decision = state["supervisor_decision"]
    if decision == "planner": return "planner"
    elif decision == "programmer": return "programmer"
    elif decision == "designer": return "designer"
    elif decision == "reporter": return "reporter"
    elif decision in ["rework"]: return "programmer"
    elif decision == "end": return END

def route_from_critic(state: GraphState):
    if state["has_error"] and state["retry_count"] < 3: return "programmer"
    return "reporter"

workflow = StateGraph(GraphState)

# Add all factory nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("planner", planner_node)
workflow.add_node("designer", designer_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

workflow.set_entry_point("supervisor")

# Supervisor conditional routing supporting the complete pipeline sequence
workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "planner": "planner",
        "programmer": "programmer",
        "designer": "designer",
        "reporter": "reporter",
        END: END
    }
)

# Return paths to supervisor after task completion
workflow.add_edge("planner", "supervisor")
workflow.add_edge("designer", "supervisor")
workflow.add_edge("reporter", "supervisor")

# Execution loop for programming and data cleaning tasks
workflow.add_edge("programmer", "executor")
workflow.add_edge("executor", "critic")

workflow.add_conditional_edges(
    "critic",
    route_from_critic,
    {"programmer": "programmer", "reporter": "reporter"}
)

if os.environ.get("LANGSMITH_API_KEY"):
    app = workflow.compile()
else:
    app = workflow.compile(checkpointer=memory)

png_bytes = app.get_graph().draw_mermaid_png()
with open("workflow_diagram.png", "wb") as f:
    f.write(png_bytes)
print("📸 Workflow diagram saved as 'workflow_diagram.png'")

user_thread_id = "user_session_123"
config = {"configurable": {"thread_id": user_thread_id}}

if __name__ == "__main__":
    mem_usage_bytes = global_df.memory_usage(deep=True).sum()
    mem_usage_mb = float(mem_usage_bytes / (1024 ** 2))
    
    buffer = io.StringIO()
    global_df.info(buf=buffer)
    schema_str = f"{buffer.getvalue()}\n\nNull Count:\n{global_df.isnull().sum()}"

    initial_state = {
        "user_query": "tell me about the dataset and give me insights from it and also create donut plot and bar chart",
        "df_schema": schema_str,
        "memory_usage_mb": mem_usage_mb,
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

    if result.get("final_report"):
        print(result["final_report"])
    else:
        print("Graph execution completed, but no final report was generated.")