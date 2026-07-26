from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.config import get_llm
from src.graph.state import GraphState
from src.graph.state_utils import get_state
from src.logs.logger import logger


class SupervisorDecision(BaseModel):
    decision: Literal[
        "planner",
        "reporter",
        "end",
    ] = Field(description="Next workflow node.")

    feedback: str = Field(
        description="""
Actionable feedback.

If planner:
Describe what additional execution or analysis is required.

If reporter:
Describe how the report should be improved.

If end:
Briefly explain why the report fully satisfies the request.
"""
    )


SYSTEM_PROMPT = """
You are the Supervisor Agent of DataScribe.

You are responsible ONLY for orchestrating the workflow.

Your job is to decide which specialist agent should work next.

You NEVER:

- write Python
- analyze datasets
- execute code
- create charts
- modify datasets
- write reports

You ONLY review the current workflow state and route the next step.

==================================================
AVAILABLE AGENTS
==================================================

PLANNER

Responsibilities

- Create or update the execution plan.
- Decide what Python analysis should be executed.
- Decide which statistics are required.
- Decide which visualizations are required.

The Planner NEVER executes Python.

--------------------------------------------------

REPORTER

Responsibilities

- Write or improve the markdown report.
- Summarize completed analysis.
- Organize report sections.
- Improve wording and readability.
- Improve formatting.
- Reference generated visualization files.
- Describe generated charts.

The Reporter CANNOT

- execute Python
- perform analysis
- calculate statistics
- create or modify charts
- generate new insights
- invent execution results
- embed interactive Plotly HTML inside markdown

==================================================
SOURCE OF TRUTH
==================================================

When making decisions, trust ONLY the workflow state provided to you.

The workflow state contains:

- User request
- Planner output
- Generated chart files
- Final report

Do NOT assume something was executed simply because the report claims it.

Generated chart files are the source of truth for visualizations.

If a visualization exists in the generated chart list, consider it successfully
generated even if it is not embedded inside the report.

==================================================
STAGE 1
(No final report exists)
==================================================

Answer one question.

Can the user's request be answered using ONLY the dataset metadata collected
during initialization?

Examples

- Dataset overview
- Dataset dimensions
- Column names
- Data types
- Missing values
- Memory usage

If YES

-> reporter

Otherwise

-> planner

Examples requiring planner

- Insights
- Statistics
- Correlations
- Charts
- Trend analysis
- Aggregations
- Dashboard
- Forecasting
- Feature engineering

When uncertain, choose planner.

==================================================
STAGE 2
(Final report exists)
==================================================

Review

- User request
- Planner output
- Generated chart files
- Final report

Answer the following questions.

Question 1

Does the completed workflow satisfy the user's request?

Use the generated chart files as evidence.

If YES

-> end

--------------------------------------------------

Question 2

If NO,

Can the report be improved WITHOUT executing new Python?

Examples

- better formatting
- better organization
- clearer explanations
- stronger executive summary
- remove duplicated text
- improve markdown
- improve descriptions of existing charts

If YES

-> reporter

--------------------------------------------------

Question 3

If additional execution is actually required,

-> planner

Examples

- requested chart was never generated
- requested analysis was never performed
- requested statistics are missing
- execution plan was insufficient
- wrong visualization was generated

Never choose planner unless another execution cycle is genuinely required.

Never choose reporter if improving the report cannot satisfy the user's request.

==================================================
RETURN
==================================================

Return ONLY:

- decision
- feedback
"""


def supervisor_node(state: GraphState) -> GraphState:
    logger.info("Supervisor evaluating workflow.")

    review_count = state.get("supervisor_review_count", 0)
    max_reviews = state.get("max_supervisor_reviews", 2)

    if state.get("final_report") and review_count >= max_reviews:

        logger.warning("Maximum supervisor reviews reached.")

        return {
            "supervisor_decision": "end",
            "supervisor_feedback": "Maximum supervisor review limit reached.",
        }

    # --------------------------------------------------
    # Stage 1
    # --------------------------------------------------

    if not state.get("final_report"):

        state_summary = f"""
USER REQUEST

{get_state(state, "user_query", "")}

INITIALIZE OUTPUT

Dataset Schema:
{get_state(state, "df_schema", "")}

Memory Usage:
{get_state(state, "memory_usage_mb", "Unknown")} MB
"""

    # --------------------------------------------------
    # Stage 2
    # --------------------------------------------------

    else:

        state_summary = f"""
USER REQUEST

{get_state(state, "user_query", "")}

PLANNER OUTPUT

{get_state(state, "plan", "No execution plan.")}

GENERATED CHARTS

{get_state(state, "chart_files", [])}

EXECUTION STATUS

{get_state(state, "execution_status", "")}

REPORTER OUTPUT

{get_state(state, "final_report", "")}
"""

    try:

        router = get_llm(state.get("api_key"), state.get("model")).with_structured_output(SupervisorDecision)

        decision = router.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=state_summary),
            ]
        )

    except Exception as exc:

        logger.exception("Supervisor routing failed.")

        return {
            "supervisor_decision": "planner",
            "supervisor_feedback": "Supervisor routing failed.",
            "fatal_error": str(exc),
        }

    updates = {
        "supervisor_decision": decision.decision,
        "supervisor_feedback": decision.feedback,
    }

    if state.get("final_report"):
        updates["supervisor_review_count"] = review_count + 1

    logger.info(
        "Supervisor selected -> %s | %s",
        decision.decision,
        decision.feedback,
    )

    return updates