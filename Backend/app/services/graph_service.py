from main_graph import app


async def run_graph(
    user_query: str,
    thread_id: str,
    api_key: str | None = None,
    model: str | None = None,
):
    """
    Runs the LangGraph workflow and yields raw LangGraph events.
    """

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    initial_state = {
        "user_query": user_query,
    }

    if api_key:
        initial_state["api_key"] = api_key

    if model:
        initial_state["model"] = model

    async for event in app.astream_events(
        initial_state,
        config=config,
        version="v2",
    ):
        yield event
