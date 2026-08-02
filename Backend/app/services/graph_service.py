from Backend.app.src.graph.graph_workflow import app
from langchain_core.runnables import RunnableConfig


async def run_graph(
    user_query: str,
    thread_id: str,
    api_key: str | None = None,
    model: str | None = None,
    dataset_path: str | None = None,
):
    """
    Runs the LangGraph workflow and yields raw LangGraph events securely.
    """

    # 1. Put the api_key in `configurable`. 
    # LangSmith NEVER logs the contents of `configurable` in state traces.
    config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "api_key": api_key,
            "model": model,
            "dataset_path": dataset_path,
        }
    }

    # 2. Build initial_state WITHOUT the api_key
    initial_state = {
        "user_query": user_query,
    }

    if model:
        initial_state["model"] = model
    if dataset_path:
        initial_state["dataset_path"] = dataset_path

    async for event in app.astream_events(
        initial_state,
        config=config,
        version="v2",
    ):
        yield event