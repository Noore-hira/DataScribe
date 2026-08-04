import io

from Backend.app.src.data_frame import load_dataframe
from Backend.app.src.graph.state import GraphState
from Backend.app.src.logs.logger import logger


def initialize_node(state: GraphState) -> GraphState:
    """
    Initialize the workflow state.
    """

    logger.info("Initializing workflow...")

    dataset_path = state.get("dataset_path")
    dataframe = load_dataframe(dataset_path)

    buffer = io.StringIO()
    dataframe.info(buf=buffer)

    schema = (
        buffer.getvalue()
        + "\n\nNull Count:\n"
        + dataframe.isnull().sum().to_string()
    )

    memory_usage_mb = (
        dataframe.memory_usage(deep=True).sum()
        / (1024 ** 2)
    )

    return {

        #Conversation
        "messages": state.get("messages", []),
        "user_query": state["user_query"],
        "session_summary": state.get("session_summary", ""),
        "recent_messages": state.get("recent_messages", []),
        "conversation_turns": state.get("conversation_turns", 0),

        # Dataset
        "df_schema": schema,
        "memory_usage_mb": float(memory_usage_mb),

        # Planning
        "plan": "",

        # Supervisor
        "supervisor_decision": None,

        # Programmer
        "generated_code": "",
        "agent_output": "",
        "previous_feedback": "",

        # Executor
        "execution_status": None,
        "execution_output": "",
        "execution_error": "",
        "chart_files": [],

        # Retry
        "retry_count": 0,
        "max_retries": 2,

        # Critic
        "critic_verdict": None,
        "critic_feedback": "",

        # Errors
        "fatal_error": "",

        # Final Report
        "final_report": "",
    }