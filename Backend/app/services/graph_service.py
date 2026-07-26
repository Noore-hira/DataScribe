from main_graph import app


async def run_graph(
    user_query: str,
    thread_id: str,
):
    """
    Runs the LangGraph workflow and yields raw LangGraph events.
    """

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    async for event in app.astream_events(
        {
            "user_query": user_query,
        },
        config=config,
        version="v2",
    ):
        yield event