import io
from dotenv import load_dotenv
import pandas as pd
from src.logs.logger import logger
from src.graph.state import GraphState, InputState
from data_frame import load_dataframe
from langgraph.graph import StateGraph, END
from src.graph.state_utils import require_state
from src.agents.executor_node import executor_node
from src.agents.supervisor_node import supervisor_node
from src.agents.critic_node import critic_node
from src.agents.planner_node import planner_node
from src.agents.designer_node import designer_node
from src.agents.reporter_node import reporter_node
from src.agents.programmer_node import programmer_node
from src.agents.initialize_node import initialize_node

load_dotenv()

def route_from_supervisor(state: GraphState):
    """Route according to the supervisor's decision."""

    decision = require_state(state, "supervisor_decision")

    logger.info("Supervisor selected '%s'.", decision)

    supervisor_routes = {
        "planner": "planner",
        "programmer": "programmer",
        "designer": "designer",
        "reporter": "reporter",
        "end": END,
    }

    if decision not in supervisor_routes:
        raise ValueError(f"Unknown supervisor decision: {decision}")

    return supervisor_routes[decision]


def route_from_critic(state: GraphState):
    """Route based on the critic's review."""

    verdict = require_state(state, "critic_verdict")

    logger.info("Critic verdict: %s", verdict.upper())

    critic_routes = {
        "pass": "supervisor",
        "fail": "programmer",
    }

    if verdict not in critic_routes:
        raise ValueError(f"Unknown critic verdict: {verdict}")

    return critic_routes[verdict]

workflow = StateGraph(GraphState, input_schema=InputState)

# Add all factory nodes
workflow.add_node("initialize", initialize_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("planner", planner_node)
workflow.add_node("designer", designer_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

workflow.set_entry_point("initialize")
workflow.add_edge("initialize", "supervisor")

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
    {
        "programmer": "programmer",
        "supervisor": "supervisor",
    },
)

# Studio manages persistence and checkpointers for graphs loaded through the
# LangGraph API. Keep this module import-safe and do not supply one here.
app = workflow.compile()

user_thread_id = "user_session_123"
config = {"configurable": {"thread_id": user_thread_id}}

if __name__ == "__main__":
    # This is a local convenience only; it must not execute during a Studio
    # graph import.
    png_bytes = app.get_graph().draw_mermaid_png()
    with open("workflow_diagram.png", "wb") as f:
        f.write(png_bytes)
    print("Workflow diagram saved as 'workflow_diagram.png'")

    initial_state = {
        "user_query":
            "tell me about the dataset and "
            "give me insights from it and "
            "also create donut plot and bar chart"
    }

    print("Starting production agentic workflow...\n")
    result = app.invoke(initial_state, config=config)
    
    print("\n" + "="*40)
    print("FINAL APPROVED REPORT")
    print("="*40)

    if result.get("final_report"):
        print(result["final_report"])
    else:
        print("Graph execution completed, but no final report was generated.")
