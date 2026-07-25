from langsmith import Client
from langsmith.evaluation import evaluate

from src.agents.conversation_node import conversation_node
from src.graph.state import GraphState

from src.evaluation.evaluators import route_evaluator


client = Client()


DATASET_NAME = "Conversation Agent Evaluation"


def conversation_target(inputs: dict):

    state: GraphState = {
        "user_query": inputs["prompt"],
        "session_summary": "",
        "recent_messages": [],
        "conversation_turns": 0,
    }

    result = conversation_node(state)

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