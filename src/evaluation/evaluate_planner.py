import pandas as pd
from dotenv import load_dotenv

from langsmith import Client, traceable

from src.agents.planner_node import planner_node
from src.evaluation.evaluators.planner_evaluators import (
    evaluate_correctness,
    evaluate_completeness,
    evaluate_relevance,
    evaluate_planning_quality,
)

load_dotenv()

client = Client()

DATASET_NAME = "Planner Evaluation"


@traceable(
    name="Planner",
    project_name="DataScribe Planner Evaluation",
)
def run_planner(user_query: str):
    """
    Executes the planner node.
    """

    state = {
        "user_query": user_query,
        "df_schema": """
Columns:
- Age (int)
- Salary (float)
- Gender (category)
- Department (category)
- Sales (float)
- Region (category)
- Date (datetime)
""",
        "plan": "",
        "supervisor_feedback": "",
    }

    result = planner_node(state)

    return result["plan"]


def main():

    dataset = client.read_dataset(
        dataset_name=DATASET_NAME,
    )

    examples = list(
        client.list_examples(
            dataset_id=dataset.id,
        )
    )

    correctness_scores = []
    completeness_scores = []
    relevance_scores = []
    planning_scores = []

    print(f"\nEvaluating {len(examples)} planner examples...\n")

    for i, example in enumerate(examples, start=1):

        query = example.inputs["user_query"]

        print(f"[{i}/{len(examples)}] {query}")

        generated_plan = run_planner(query)

        correctness = evaluate_correctness(
            query,
            generated_plan,
        )

        completeness = evaluate_completeness(
            query,
            generated_plan,
        )

        relevance = evaluate_relevance(
            query,
            generated_plan,
        )

        planning = evaluate_planning_quality(
            query,
            generated_plan,
        )

        correctness_scores.append(correctness.score)
        completeness_scores.append(completeness.score)
        relevance_scores.append(relevance.score)
        planning_scores.append(planning.score)

        print(f"Correctness      : {correctness.score}/5")
        print(f"Completeness     : {completeness.score}/5")
        print(f"Relevance        : {relevance.score}/5")
        print(f"Planning Quality : {planning.score}/5")
        print("-" * 60)

    results = pd.DataFrame(
        {
            "Correctness": correctness_scores,
            "Completeness": completeness_scores,
            "Relevance": relevance_scores,
            "Planning Quality": planning_scores,
        }
    )

    print("\n================ FINAL RESULTS ================\n")

    print(results.mean())

    print("\nOverall Score:",
          round(results.mean().mean(), 2),
          "/ 5")

    results.to_csv(
        "planner_evaluation_results.csv",
        index=False,
    )

    print("\nResults saved to planner_evaluation_results.csv")


if __name__ == "__main__":
    main()