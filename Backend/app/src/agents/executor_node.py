import os
import re
import base64
from dotenv import load_dotenv

load_dotenv()

from e2b_code_interpreter import Sandbox

from Backend.app.src.graph.state import GraphState
from Backend.app.src.graph.state_utils import require_state
from Backend.app.src.logs.logger import logger


def executor_node(state: GraphState) -> GraphState:
    """
    Execute generated Python code inside an E2B sandbox.

    Supports:

    • matplotlib
    • seaborn
    • plotly html
    • plotly animations

    Automatically downloads every generated chart from the sandbox.
    """

    logger.info("Executor started: Routing to E2B Sandbox.")

    code = require_state(state, "generated_code")
    dataset_path = state.get("dataset_path")

    if not code.strip():
        return {
            "execution_status": "failed",
            "execution_error": "No generated code.",
            "execution_output": "",
            "chart_files": [],
        }

    artifact_dir = os.environ.get(
        "LANGGRAPH_ARTIFACTS_DIR",
        "charts",
    )

    os.makedirs(artifact_dir, exist_ok=True)

    code = re.sub(r"```python|```", "", code)

    dataset_filename = (
        os.path.basename(dataset_path)
        if dataset_path
        else "dataset.csv"
    )

    sandbox_dataset = f"/tmp/{dataset_filename}"

    try:

        with Sandbox.create() as sandbox:

            logger.info("Created E2B sandbox.")

            ####################################################
            # Upload dataset
            ####################################################

            if dataset_path and os.path.exists(dataset_path):

                with open(dataset_path, "rb") as f:
                    sandbox.files.write(
                        sandbox_dataset,
                        f.read(),
                    )

                logger.info(
                    f"Uploaded dataset -> {sandbox_dataset}"
                )

                setup = f"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

global_df_path = "{sandbox_dataset}"
global_df = pd.read_csv(global_df_path)
df = global_df
"""

            else:

                setup = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
"""

            final_code = setup + "\n" + code

            ####################################################
            # Execute
            ####################################################

            execution = sandbox.run_code(final_code)
            logger.info("Execution stdout:")
            logger.info(execution.text)

            logger.info(
                f"E2B returned {len(execution.results)} result objects."
            )

            ####################################################
            # Error
            ####################################################

            if execution.error:

                err = (
                    f"{execution.error.name}: "
                    f"{execution.error.value}"
                )

                logger.error(err)

                return {
                    "execution_status": "failed",
                    "execution_error": err,
                    "execution_output": execution.text or "",
                    "chart_files": [],
                }

            ####################################################
            # Collect charts
            ####################################################

            chart_files = []

            logger.info(
                f"E2B returned {len(execution.results)} result objects."
            )

            ####################################################
            # Save inline results
            ####################################################

            for i, result in enumerate(execution.results):

                if getattr(result, "png", None):

                    filename = f"chart_{i}.png"

                    with open(
                        os.path.join(
                            artifact_dir,
                            filename,
                        ),
                        "wb",
                    ) as f:

                        f.write(
                            base64.b64decode(result.png)
                        )

                    chart_files.append(filename)

                    logger.info(
                        f"Saved inline PNG -> {filename}"
                    )

                if getattr(result, "html", None):

                    filename = f"chart_{i}.html"

                    with open(
                        os.path.join(
                            artifact_dir,
                            filename,
                        ),
                        "w",
                        encoding="utf-8",
                    ) as f:

                        f.write(result.html)

                    chart_files.append(filename)

                    logger.info(
                        f"Saved inline HTML -> {filename}"
                    )

            ####################################################
            # Search sandbox recursively
            ####################################################

            logger.info("Searching sandbox recursively for generated charts...")

            downloaded = set()

            try:
                find_result = sandbox.commands.run(
                    "find /tmp /home/user . -type f "
                    "\\( "
                    "-iname '*.html' -o "
                    "-iname '*.png' -o "
                    "-iname '*.jpg' -o "
                    "-iname '*.jpeg' -o "
                    "-iname '*.svg' "
                    "\\) 2>/dev/null"
                )

                paths = [
                    p.strip()
                    for p in find_result.stdout.splitlines()
                    if p.strip()
                ]

                logger.info(f"Found {len(paths)} generated files.")

                for path in paths:

                    filename = os.path.basename(path)

                    if filename in downloaded:
                        continue

                    logger.info(f"Downloading {path}")

                    try:

                        data = sandbox.files.read(path)

                        local_path = os.path.join(
                            artifact_dir,
                            filename,
                        )

                        if filename.lower().endswith(".html"):

                            if isinstance(data, bytes):
                                data = data.decode("utf-8")

                            with open(
                                local_path,
                                "w",
                                encoding="utf-8",
                            ) as f:
                                f.write(data)

                        else:

                            if isinstance(data, str):
                                data = data.encode()

                            with open(local_path, "wb") as f:
                                f.write(data)

                        downloaded.add(filename)

                        if filename not in chart_files:
                            chart_files.append(filename)

                        logger.info(f"Downloaded {filename}")

                    except Exception as e:

                        logger.warning(
                            f"Unable to download {path}: {e}"
                        )

            except Exception as e:

                logger.warning(
                    f"Recursive chart search failed: {e}"
                )
            ####################################################
            # Done
            ####################################################

            logger.info(
                f"Execution complete. "
                f"Saved {len(chart_files)} charts."
            )

            return {
                "execution_status": "success",
                "execution_output": execution.text.strip()
                if execution.text
                else "",
                "execution_error": "",
                "chart_files": chart_files,
                "executor_metrics": {
                    "success": True,
                    "charts": len(chart_files),
                },
            }

    except Exception as exc:

        logger.exception("Executor crashed.")

        return {
            "execution_status": "failed",
            "execution_error": str(exc),
            "execution_output": "",
            "chart_files": [],
        }