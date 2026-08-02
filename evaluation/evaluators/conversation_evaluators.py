from langsmith.evaluation import EvaluationResult


def route_evaluator(run, example):

    predicted = run.outputs["route"]
    expected = example.outputs["expected_route"]

    return EvaluationResult(
        key="route_correct",
        score=float(predicted == expected),
        comment=f"Expected={expected}, Predicted={predicted}",
    )