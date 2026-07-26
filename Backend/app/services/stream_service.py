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


async def stream_chat(
    query: str,
    thread_id: str,
):

    start = time.perf_counter()

    async for event in run_graph(
        query,
        thread_id,
    ):

        event_type = event.get("event")
        node = event.get("name")

        if node not in GRAPH_NODES:
            continue

        # ---------------- START ----------------

        if event_type == "on_chain_start":

            yield sse(
                "node_start",
                node=node,
                progress=NODE_PROGRESS[node],
                message=NODE_MESSAGES[node][0],
            )

        # ---------------- END ----------------

        elif event_type == "on_chain_end":

            output = event.get(
                "data",
                {},
            ).get(
                "output",
                {},
            )

            yield sse(
                "node_end",
                node=node,
                metrics=extract_metrics(
                    node,
                    output,
                ),
                progress=NODE_PROGRESS[node],
                message=NODE_MESSAGES[node][1],
            )

            if node == "supervisor":

                yield sse(
                    "decision",
                    decision=output.get(
                        "supervisor_decision"
                    ),
                )

            if node == "planner":

                yield sse(
                    "plan",
                    plan=output.get(
                        "plan",
                        "",
                    ),
                )

            if node == "programmer":

                yield sse(
                    "code",
                    code=output.get(
                        "generated_code",
                        "",
                    ),
                )

            if node == "executor":

                yield sse(
                    "execution",
                    output=output.get(
                        "execution_output",
                        "",
                    ),
                )

                if output.get("chart_files"):

                    yield sse(
                        "charts",
                        charts=output.get(
                            "chart_files",
                            [],
                        ),
                    )

            if node == "critic":

                yield sse(
                    "critic",
                    verdict=output.get(
                        "critic_verdict"
                    ),
                    retry=output.get(
                        "retry_count",
                        0,
                    ),
                )

                if output.get(
                    "critic_verdict"
                ) == "fail":

                    yield sse(
                        "retry",
                        retry=output.get(
                            "retry_count",
                            0,
                        ),
                        next_node="programmer",
                        message="Retrying analysis...",
                    )

            if output.get(
                "final_report"
            ):

                yield sse(
                    "report",
                    report=output[
                        "final_report"
                    ],
                    charts=output.get(
                        "chart_files",
                        [],
                    ),
                )

        # ---------------- ERROR ----------------

        elif event_type == "on_chain_error":

            yield sse(
                "error",
                node=node,
                message="Node execution failed.",
            )

    yield sse(
        "complete",
        duration=round(
            time.perf_counter() - start,
            2,
        ),
    )