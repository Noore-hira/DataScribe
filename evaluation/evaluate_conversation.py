import os
import sys
from pathlib import Path
from langsmith import Client
from langsmith.evaluation import evaluate
from dotenv import load_dotenv

# Setup path so Python can find the 'Backend' module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from Backend.app.src.agents.conversation_node import conversation_node
from Backend.app.src.graph.state import GraphState
from evaluation.evaluators.conversation_evaluators import route_evaluator

load_dotenv()
client = Client()


DATASET_NAME = "Conversation Agent Evaluation"


def conversation_target(inputs: dict):

    state: GraphState = {
        "user_query": inputs["prompt"],
        "session_summary": "",
        "recent_messages": [],
        "conversation_turns": 0,
    }
    config = {
        "configurable": {
            "thread_id": "workflow_eval",
            "api_key": os.getenv("GROQ_API_KEY"),
        }
    }
    result = conversation_node(state, config)

    return {
        "route": result["conversation_route"],
    }


experiment_results = evaluate(

    conversation_target,

    data=DATASET_NAME,

    evaluators=[
        route_evaluator,
    ],

    experiment_prefix="conversation-routing",

)

print(experiment_results)