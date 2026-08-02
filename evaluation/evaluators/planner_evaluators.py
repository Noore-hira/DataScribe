from DataScribe.Backend.app.src.evaluation.judge import judge


CORRECTNESS_PROMPT = """
You are an expert evaluator assessing execution plans.

Determine whether the generated plan correctly captures
the user's request.

Scoring

5 = Fully correct

4 = Mostly correct

3 = Partially correct

2 = Mostly incorrect

1 = Completely incorrect
"""


COMPLETENESS_PROMPT = """
Determine whether the planner missed important analysis,
statistics or visualization tasks.

Scoring

5 = Complete

4 = Nearly complete

3 = Some missing tasks

2 = Many missing tasks

1 = Missing most tasks
"""


RELEVANCE_PROMPT = """
Determine whether every task in the execution plan
is relevant to the user's request.

Penalize:

- unnecessary analysis
- unnecessary charts
- unrelated workflow stages

Scoring

5 = Perfectly focused

4 = Mostly focused

3 = Some irrelevant tasks

2 = Many irrelevant tasks

1 = Mostly irrelevant
"""


PLANNING_QUALITY_PROMPT = """
Evaluate the quality of the execution plan.

Consider

- logical decomposition
- execution order
- dependency handling
- workflow organization

Scoring

5 = Excellent

4 = Good

3 = Acceptable

2 = Weak

1 = Poor
"""


def evaluate_correctness(query, plan):

    return judge(
        CORRECTNESS_PROMPT,
        f"""
User Request

{query}

Execution Plan

{plan}
""",
    )


def evaluate_completeness(query, plan):

    return judge(
        COMPLETENESS_PROMPT,
        f"""
User Request

{query}

Execution Plan

{plan}
""",
    )


def evaluate_relevance(query, plan):

    return judge(
        RELEVANCE_PROMPT,
        f"""
User Request

{query}

Execution Plan

{plan}
""",
    )


def evaluate_planning_quality(query, plan):

    return judge(
        PLANNING_QUALITY_PROMPT,
        f"""
User Request

{query}

Execution Plan

{plan}
""",
    )