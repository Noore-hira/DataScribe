from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from Backend.app.src.agents.conversation_node import conversation_node
from Backend.app.src.agents.critic_node import critic_node
from Backend.app.src.agents.executor_node import executor_node
from Backend.app.src.agents.initialize_node import initialize_node
from Backend.app.src.agents.planner_node import planner_node
from Backend.app.src.agents.programmer_node import programmer_node
from Backend.app.src.agents.reporter_node import reporter_node
from Backend.app.src.agents.supervisor_node import supervisor_node
from Backend.app.src.graph.state import GraphState
from Backend.app.src.graph.state_utils import require_state
from Backend.app.src.logs.logger import logger

load_dotenv()

# ----------------------------------------------------
# Routing
# ----------------------------------------------------

def route_conversation(state: GraphState) -> str:
    return state["conversation_route"]


def route_from_supervisor(state: GraphState) -> str:
    decision = require_state(state, "supervisor_decision")

    logger.info("Supervisor routing -> %s", decision)

    return decision


def route_from_critic(state: GraphState) -> str:
    verdict = require_state(state, "critic_verdict")

    logger.info(
        "Critic routing -> verdict=%s | retry=%d/%d",
        verdict,
        state.get("retry_count", 0),
        state.get("max_retries", 2),
    )

    if verdict == "fail":
        logger.info("Critic requested another programming iteration.")
        return "programmer"

    if verdict == "pass":
        logger.info("Critic approved execution.")
        return "reporter"

    if verdict == "abort":
        logger.warning(
            "Maximum retries reached. Generating partial report."
        )
        return "reporter"

    logger.warning(
        "Unknown critic verdict '%s'. Routing to reporter.",
        verdict,
    )
    return "reporter"


# ----------------------------------------------------
# Graph
# ----------------------------------------------------

memory = MemorySaver()

workflow = StateGraph(GraphState)

workflow.add_node("conversation", conversation_node)
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

workflow.set_entry_point("conversation")

workflow.add_conditional_edges(
    "conversation",
    route_conversation,
    {
        "initialize": "initialize",
        "answer": END,
        "reject": END,
    },
)

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

# Reporter always sends the final report to the supervisor
# for one final review. The supervisor then ends the workflow.
workflow.add_edge("reporter", "supervisor")

# ----------------------------------------------------

app = workflow.compile(
    checkpointer=memory,
)

# ----------------------------------------------------
# Local Testing
# ----------------------------------------------------

if __name__ == "__main__":

    logger.info("Generating workflow diagram...")

    with open("workflow_diagram.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())

    logger.info("Workflow diagram saved as workflow_diagram.png")

    while True:
        user_input = input("Ask question (or 'q' to quit): ")

        if user_input.lower() == "q":
            break

        result = app.invoke(
            {
                "user_query": user_input,
            },
            config={
                "configurable": {
                    "thread_id": "test_session_001",
                },
            },
        )

        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(result.get("final_report", "No report generated."))

        print("\n" + "=" * 60)
        print("WORKFLOW STATE")
        print("=" * 60)

        print(
            {
                "supervisor": result.get("supervisor_decision"),
                "planner": bool(result.get("plan")),
                "critic": result.get("critic_verdict"),
                "retry_count": result.get("retry_count"),
                "execution_status": result.get("execution_status"),
                "charts": len(result.get("chart_files", [])),
                "error": result.get("execution_error"),
            }
        )