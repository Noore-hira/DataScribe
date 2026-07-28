from Backend.app.src.graph.graph_workflow import app


async def run_graph(
    user_query: str,
    thread_id: str,
    api_key: str | None = None,
    model: str | None = None,
    dataset_path: str | None = None,
):
    """
    Runs the LangGraph workflow and yields raw LangGraph events.
    """

    config = {
        "configurable": {
            "thread_id": thread_id,
            "api_key": api_key,
            "model": model,
            "dataset_path": dataset_path, # <-- Added this!
        }
    }

    initial_state = {
        "user_query": user_query,
    }

    # You are also injecting these into the state, which is great!
    if api_key:
        initial_state["api_key"] = api_key
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