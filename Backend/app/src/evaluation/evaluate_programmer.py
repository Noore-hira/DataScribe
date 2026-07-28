from dotenv import load_dotenv

from langsmith import Client, traceable

from DataScribe.Backend.app.src.agents.planner_node import planner_node
from DataScribe.Backend.app.src.agents.programmer_node import programmer_node

from DataScribe.Backend.app.src.evaluation.evaluators.programmer_evaluators import (
    evaluate_correctness,
    evaluate_executability,
    evaluate_safety,
    evaluate_code_quality,
    evaluate_plan_adherence,
)

load_dotenv()

client = Client()

DATASET_NAME = "Programmer Evaluation"


@traceable(
    name="Programmer",
    project_name="DataScribe Programmer Evaluation",
)
def run_programmer(
    user_query: str,
    df_schema: str,
):
    """
    Runs planner + programmer.

    We evaluate ONLY the programmer output,
    but still use the planner to generate the plan.
    """

    # -------------------------------
    # Planner
    # -------------------------------

    planner_state = {
        "user_query": user_query,
        "df_schema": df_schema,
        "plan": "",
        "supervisor_feedback": "",
    }

    planner_result = planner_node(planner_state)

    # -------------------------------
    # Programmer
    # -------------------------------

    programmer_state = {
        **planner_state,
        **planner_result,
    }

    programmer_result = programmer_node(
        programmer_state
    )

    return {
        "plan": programmer_result["plan"],
        "generated_code": programmer_result["generated_code"],
    }


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
    executability_scores = []
    safety_scores = []
    quality_scores = []
    adherence_scores = []

    print(
        f"\nEvaluating {len(examples)} programmer examples...\n"
    )

    for idx, example in enumerate(examples, start=1):

        query = example.inputs["user_query"]

        schema = example.inputs["df_schema"]

        print(
            f"[{idx}/{len(examples)}] {query}"
        )

        result = run_programmer(
            query,
            schema,
        )

        generated_code = result["generated_code"]

        plan = result["plan"]

        correctness = evaluate_correctness(
            query,
            plan,
            generated_code,
        )

        executability = evaluate_executability(
            query,
            plan,
            generated_code,
        )

        safety = evaluate_safety(
            query,
            plan,
            generated_code,
        )

        quality = evaluate_code_quality(
            query,
            plan,
            generated_code,
        )

        adherence = evaluate_plan_adherence(
            query,
            plan,
            generated_code,
        )

        correctness_scores.append(
            correctness.score
        )

        executability_scores.append(
            executability.score
        )

        safety_scores.append(
            safety.score
        )

        quality_scores.append(
            quality.score
        )

        adherence_scores.append(
            adherence.score
        )

        print(
            f"Correctness      : {correctness.score}/5"
        )

        print(
            f"Executability    : {executability.score}/5"
        )

        print(
            f"Safety           : {safety.score}/5"
        )

        print(
            f"Code Quality     : {quality.score}/5"
        )

        print(
            f"Plan Adherence   : {adherence.score}/5"
        )

        print("-" * 60)

    print("\n============================")
    print("FINAL RESULTS")
    print("============================\n")

    print(
        f"Correctness     : {sum(correctness_scores)/len(correctness_scores):.2f}"
    )

    print(
        f"Executability   : {sum(executability_scores)/len(executability_scores):.2f}"
    )

    print(
        f"Safety          : {sum(safety_scores)/len(safety_scores):.2f}"
    )

    print(
        f"Code Quality    : {sum(quality_scores)/len(quality_scores):.2f}"
    )

    print(
        f"Plan Adherence  : {sum(adherence_scores)/len(adherence_scores):.2f}"
    )

    overall = (
        sum(correctness_scores)
        + sum(executability_scores)
        + sum(safety_scores)
        + sum(quality_scores)
        + sum(adherence_scores)
    ) / (
        5 * len(correctness_scores)
    )

    print(
        f"\nOverall Score : {overall:.2f}/5"
    )


if __name__ == "__main__":
    main()