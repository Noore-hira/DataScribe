from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from src.agents.critic_node import critic_node
from src.agents.executor_node import executor_node
from src.agents.initialize_node import initialize_node
from src.agents.planner_node import planner_node
from src.agents.programmer_node import programmer_node
from src.agents.reporter_node import reporter_node
from src.agents.supervisor_node import supervisor_node
from src.graph.state import GraphState
from src.graph.state_utils import require_state
from src.logs.logger import logger

load_dotenv()


# ----------------------------------------------------
# Routing
# ----------------------------------------------------

def route_from_supervisor(state: GraphState) -> str:
    decision = require_state(state, "supervisor_decision")

    logger.info("Supervisor routing -> %s", decision)

    return decision


def route_from_critic(state: GraphState) -> str:
    verdict = require_state(state, "critic_verdict")

    logger.info(
        "Critic verdict -> %s (retry=%d)",
        verdict,
        state.get("retry_count", 0),
    )

    if verdict == "fail":
        return "programmer"

    return "reporter"


# ----------------------------------------------------
# Graph
# ----------------------------------------------------

workflow = StateGraph(GraphState)

workflow.add_node("initialize", initialize_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("planner", planner_node)
workflow.add_node("programmer", programmer_node)
workflow.add_node("executor", executor_node)
workflow.add_node("critic", critic_node)
workflow.add_node("reporter", reporter_node)

# ----------------------------------------------------
# Entry
# ----------------------------------------------------

workflow.set_entry_point("initialize")

workflow.add_edge("initialize", "supervisor")

# ----------------------------------------------------
# Supervisor
# ----------------------------------------------------

workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "planner": "planner",
        "reporter": "reporter",
        "end": END,
    },
)

# ----------------------------------------------------
# Planner Pipeline
# ----------------------------------------------------

workflow.add_edge("planner", "programmer")

workflow.add_edge("programmer", "executor")

workflow.add_edge("executor", "critic")

# ----------------------------------------------------
# Critic
# ----------------------------------------------------

workflow.add_conditional_edges(
    "critic",
    route_from_critic,
    {
        "programmer": "programmer",
        "reporter": "reporter",
    },
)

# ----------------------------------------------------
# Reporter
# ----------------------------------------------------

# The Supervisor reviews every report before ending.
workflow.add_edge("reporter", "supervisor")

# ----------------------------------------------------

app = workflow.compile()


if __name__ == "__main__":

    logger.info("Generating workflow diagram...")

    with open("workflow_diagram.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())

    logger.info("Workflow diagram saved as workflow_diagram.png")

    user_query = ("give me overview of dataset")

    logger.info("Starting workflow execution...")

    result = app.invoke(
        {
            "user_query": user_query,
        },
        config={
            "configurable": {
                "thread_id": "test_session_001",
            }
        },
    )

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)

    print(
        result.get(
            "final_report",
            "Workflow completed but no report was generated.",
        )
    )

    print("\n" + "=" * 60)
    print("WORKFLOW STATE")
    print("=" * 60)

    print(
        {
            "supervisor": result.get("supervisor_decision"),
            "supervisor_reviews": result.get("supervisor_review_count"),
            "planner": bool(result.get("plan")),
            "critic": result.get("critic_verdict"),
            "retry_count": result.get("retry_count"),
            "execution_status": result.get("execution_status"),
            "charts": len(result.get("chart_files", [])),
            "error": result.get("execution_error"),
        }
    )