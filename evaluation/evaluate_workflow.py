import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from evaluators.workflow_evaluators import evaluate_workflow_metrics

# Setup path so Python can find the 'Backend' module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()
# Initialize LangSmith Client
client = Client()

from Backend.app.src.graph.graph_workflow import app
def run_workflow(inputs):
    time.sleep(30)
    state = {
        "user_query": inputs["user_query"],
        "dataset_path": inputs["dataset_name"],
    }

    config = {
        "configurable": {
            "thread_id": "workflow_eval",
            "api_key": os.getenv("GROQ_API_KEY"),
        }
    }

    try:

        result = app.invoke(
            state,
            config=config,
        )

        return {

            "conversation_route":
                result.get("conversation_route"),

            "supervisor_decision":
                result.get("supervisor_decision"),

            "plan":
                result.get("plan"),

            "generated_code":
                result.get("generated_code"),

            "execution_status":
                result.get("execution_status"),

            "execution_error":
                result.get("execution_error"),

            "execution_output":
                result.get("execution_output"),

            "chart_files":
                result.get("chart_files", []),

            "critic_verdict":
                result.get("critic_verdict"),

            "retry_count":
                result.get("retry_count"),

            "final_report":
                result.get("final_report"),
        }

    except Exception as e:

        return {
            "workflow_error": str(e)
        }

# ==========================================
# 3. Execute Workflow Evaluation
# ==========================================
if __name__ == "__main__":

    print("=" * 60)
    print("Starting Complete Workflow Evaluation...")
    print("=" * 60)

    experiment_results = evaluate(
        run_workflow,                      # <-- Full LangGraph workflow
        data="Workflow Evaluation",        # <-- LangSmith dataset
        evaluators=[evaluate_workflow_metrics],
        experiment_prefix="workflow-evaluation",
    )

    print("\nEvaluation complete!")