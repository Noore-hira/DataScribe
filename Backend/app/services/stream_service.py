import asyncio
import json
import time
from datetime import datetime

from Backend.app.services.graph_service import run_graph


GRAPH_NODES = {
    "conversation",
    "initialize",
    "supervisor",
    "planner",
    "programmer",
    "executor",
    "critic",
    "reporter",
}


NODE_PROGRESS = {
    "conversation": 10,
    "initialize": 20,
    "supervisor": 30,
    "planner": 45,
    "programmer": 60,
    "executor": 80,
    "critic": 90,
    "reporter": 100,
}


NODE_MESSAGES = {
    "conversation": (
        "Understanding your request...",
        "Conversation routing completed.",
    ),
    "initialize": (
        "Loading dataset...",
        "Dataset initialized.",
    ),
    "supervisor": (
        "Supervisor reviewing workflow...",
        "Supervisor finished.",
    ),
    "planner": (
        "Creating execution plan...",
        "Execution plan created.",
    ),
    "programmer": (
        "Generating Python code...",
        "Code generation completed.",
    ),
    "executor": (
        "Executing analysis...",
        "Execution completed.",
    ),
    "critic": (
        "Reviewing execution...",
        "Quality review completed.",
    ),
    "reporter": (
        "Generating report...",
        "Final report generated.",
    ),
}


# Heartbeat interval (seconds) to keep SSE connection alive
# during long-running LLM operations
HEARTBEAT_INTERVAL = 10


def sse(event: str, **data):

    return {
        "event": event,
        "data": json.dumps(
            {
                "timestamp": datetime.utcnow().isoformat(),
                **data,
            }
        ),
    }


def extract_metrics(node: str, output: dict):

    if not isinstance(output, dict):
        return {}

    if node == "conversation":
        return {
            "route": output.get("conversation_route"),
            "turns": output.get("conversation_turns"),
        }

    if node == "initialize":
        return {
            "dataset_loaded": bool(
                output.get("df_schema")
            )
        }

    if node == "supervisor":
        return {
            "decision": output.get(
                "supervisor_decision"
            ),
            "reviews": output.get(
                "supervisor_review_count",
                0,
            ),
        }

    if node == "planner":
        return {
            "plan_created": bool(
                output.get("plan")
            )
        }

    if node == "programmer":

        code = output.get(
            "generated_code",
            ""
        )

        return {
            "generated": bool(code),
            "lines": len(code.splitlines()),
        }

    if node == "executor":
        return {
            "status": output.get(
                "execution_status"
            ),
            "charts": len(
                output.get(
                    "chart_files",
                    [],
                )
            ),
        }

    if node == "critic":
        return {
            "verdict": output.get(
                "critic_verdict"
            ),
            "retry": output.get(
                "retry_count",
                0,
            ),
        }

    if node == "reporter":

        report = output.get(
            "final_report",
            "",
        )

        return {
            "generated": bool(report),
            "length": len(report),
        }

    return {}


def _process_graph_event(event: dict):
    """
    Process a single LangGraph event and return a list of
    SSE event dicts to yield. Returns an empty list if the
    event should be skipped.
    """
    event_type = event.get("event")
    node = event.get("name")

    if node not in GRAPH_NODES:
        return []

    results = []

    # ---------------- START ----------------

    if event_type == "on_chain_start":

        results.append(sse(
            "node_start",
            node=node,
            progress=NODE_PROGRESS[node],
            message=NODE_MESSAGES[node][0],
        ))

    # ---------------- END ----------------

    elif event_type == "on_chain_end":

        output = event.get(
            "data",
            {},
        ).get(
            "output",
            {},
        )

        results.append(sse(
            "node_end",
            node=node,
            metrics=extract_metrics(
                node,
                output,
            ),
            progress=NODE_PROGRESS[node],
            message=NODE_MESSAGES[node][1],
        ))

        if node == "supervisor":

            results.append(sse(
                "decision",
                decision=output.get(
                    "supervisor_decision"
                ),
            ))

        if node == "planner":

            results.append(sse(
                "plan",
                plan=output.get(
                    "plan",
                    "",
                ),
            ))

        if node == "programmer":

            results.append(sse(
                "code",
                code=output.get(
                    "generated_code",
                    "",
                ),
            ))

        if node == "executor":

            results.append(sse(
                "execution",
                output=output.get(
                    "execution_output",
                    "",
                ),
            ))

            if output.get("chart_files"):

                results.append(sse(
                    "charts",
                    charts=output.get(
                        "chart_files",
                        [],
                    ),
                ))

        if node == "critic":

            results.append(sse(
                "critic",
                verdict=output.get(
                    "critic_verdict"
                ),
                retry=output.get(
                    "retry_count",
                    0,
                ),
            ))

            if output.get(
                "critic_verdict"
            ) == "fail":

                results.append(sse(
                    "retry",
                    retry_count=output.get(
                        "retry_count",
                        0,
                    ),
                    next_node="programmer",
                    message="Retrying analysis...",
                ))

        if output.get(
            "final_report"
        ):

            results.append(sse(
                "report",
                report=output[
                    "final_report"
                ],
                charts=output.get(
                    "chart_files",
                    [],
                ),
            ))

    # ---------------- ERROR ----------------

    elif event_type == "on_chain_error":

        results.append(sse(
            "error",
            node=node,
            message="Node execution failed.",
        ))

    return results


async def stream_chat(
    query: str,
    thread_id: str,
    api_key: str | None = None,
    model: str | None = None,
):

    start = time.perf_counter()

    # --------------------------------------------------
    # Use an asyncio.Queue to interleave heartbeat events
    # with graph events. This keeps the SSE connection
    # alive during long-running LLM operations.
    # --------------------------------------------------
    queue: asyncio.Queue = asyncio.Queue()
    graph_done = asyncio.Event()

    # Heartbeat producer: sends heartbeat events at
    # regular intervals while the graph is running
    async def heartbeat_producer():
        while not graph_done.is_set():
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await queue.put(("heartbeat", None))

    # Graph event producer: runs the LangGraph workflow
    # and puts events into the queue
    async def graph_producer():
        try:
            async for event in run_graph(
                query,
                thread_id,
                api_key=api_key,
                model=model,
            ):
                await queue.put(("graph", event))
        except Exception as e:
            # --------------------------------------------------
            # If the graph execution fails, send an error event
            # to the client instead of silently closing the
            # connection (which would trigger a reconnect loop)
            # --------------------------------------------------
            await queue.put(("error", e))
        finally:
            graph_done.set()

    heartbeat_task = asyncio.create_task(heartbeat_producer())
    graph_task = asyncio.create_task(graph_producer())

    try:
        # --------------------------------------------------
        # Consume events from the queue until the graph is
        # done AND all queued events have been processed
        # --------------------------------------------------
        while not (graph_done.is_set() and queue.empty()):
            try:
                item_type, item = await asyncio.wait_for(
                    queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                # No event available within 1 second;
                # loop back and check again
                continue

            if item_type == "heartbeat":
                yield sse("heartbeat")

            elif item_type == "graph":
                for sse_event in _process_graph_event(item):
                    yield sse_event

            elif item_type == "error":
                yield sse(
                    "error",
                    message=f"Workflow error: {str(item)}",
                )

    finally:
        # --------------------------------------------------
        # Clean up background tasks
        # --------------------------------------------------
        heartbeat_task.cancel()
        graph_task.cancel()
        for task in (heartbeat_task, graph_task):
            try:
                await task
            except asyncio.CancelledError:
                pass

    yield sse(
        "complete",
        duration=round(
            time.perf_counter() - start,
            2,
        ),
    )
