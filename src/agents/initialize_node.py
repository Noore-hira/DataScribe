import io

from data_frame import load_dataframe
from src.graph.state import GraphState, InputState
from src.logs.logger import logger


def initialize_node(state: InputState) -> GraphState:
    """
    Initializes the workflow state.

    Runs exactly once at the beginning of every graph execution.
    Responsible for preparing dataset metadata and default state values.
    """
    logger.info("Initializing workflow...")

    dataframe = load_dataframe()

    # Dataset schema
    buffer = io.StringIO()
    dataframe.info(buf=buffer)

    schema = (
        f"{buffer.getvalue()}\n\n"
        f"Null Count:\n{dataframe.isnull().sum()}"
    )

    memory_usage_mb = float(
        dataframe.memory_usage(deep=True).sum()
        / (1024 ** 2)
    )

    return {
        "user_query": state["user_query"],

        # dataset metadata
        "df_schema": schema,
        "memory_usage_mb": memory_usage_mb,

        # execution state
        "retry_count": 0,
        "revision_count": 0,
        "has_error": False,
        "execution_output": "",

        # visualization
        "charts_completed": False,
        "chart_files": [],

        # workflow
        "plan": None,
        "current_code": None,
        "supervisor_decision": None,
        "fatal_error": None,
        "final_report": None,
    }