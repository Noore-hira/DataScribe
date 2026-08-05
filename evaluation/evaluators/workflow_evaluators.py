from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class WorkflowEvaluation(BaseModel):
    routing: int = Field(..., ge=1, le=5)
    planning: int = Field(..., ge=1, le=5)
    execution: int = Field(..., ge=1, le=5)
    reporting: int = Field(..., ge=1, le=5)
    overall: int = Field(..., ge=1, le=5)
    routing_reason: str
    planning_reason: str
    execution_reason: str
    reporting_reason: str
    overall_reason: str

judge_llm = ChatGroq(model="llama-3.3-70b-versatile",temperature=0)

judge = judge_llm.with_structured_output(WorkflowEvaluation)

def evaluate_workflow_metrics(run, example) -> list[dict]:
    """
    Evaluate the complete DataScribe workflow.
    """

    expected = example.outputs
    user_query = example.inputs["user_query"]

    outputs = run.outputs or {}

    if outputs.get("workflow_error"):
        error = outputs["workflow_error"]

        return [
            {"key": "Routing_Score", "score": 1, "comment": error},
            {"key": "Planning_Score", "score": 1, "comment": error},
            {"key": "Execution_Score", "score": 1, "comment": error},
            {"key": "Reporting_Score", "score": 1, "comment": error},
            {"key": "Overall_Score", "score": 1, "comment": error},
        ]

    prompt = PromptTemplate.from_template(
        """
You are evaluating the COMPLETE execution of an AI data analysis workflow.

The workflow consists of:

Conversation
→ Initialize
→ Supervisor
→ Planner
→ Programmer
→ Executor
→ Critic
→ Reporter

Do NOT compare outputs literally.

Reward semantically equivalent solutions.

Ignore:

- wording differences
- formatting
- variable names
- ordering of valid steps
- different but equivalent implementations

=============================
USER QUERY
=============================

{user_query}

=============================
EXPECTED
=============================

Conversation Route:
{expected_route}

Planning Keywords:
{expected_plan_keywords}

Execution Status:
{expected_execution_status}

Expected Chart Count:
{expected_chart_count}

Expected Chart Types:
{expected_chart_types}

Expected Report Keywords:
{expected_report_keywords}

Expected Critic Verdict:
{expected_critic_verdict}

Expected Retry Count:
{expected_retry_count}

Expected Final Supervisor Decision:
{expected_final_supervisor_decision}

=============================
GENERATED
=============================

Conversation Route:
{conversation_route}

Supervisor Decision:
{supervisor_decision}

Generated Plan:
{plan}

Execution Status:
{execution_status}

Execution Error:
{execution_error}

Charts:
{chart_files}

Critic Verdict:
{critic_verdict}

Retry Count:
{retry_count}

Final Report:
{final_report}

=============================
Evaluate FIVE metrics.

ROUTING

5 = Correct conversation route and supervisor decision.

4 = Minor routing issue.

3 = Partially correct.

2 = Mostly incorrect.

1 = Wrong routing.


PLANNING

Judge whether the generated plan contains the major analytical steps required.

Ignore wording differences.

5 = Excellent

1 = Poor


EXECUTION

Consider:

• Execution succeeded

• Requested analysis performed

• Correct visualizations generated

• Chart count is reasonable

• Critic verdict

• Retry behaviour

• No significant execution errors

5 = Fully successful

1 = Failed


REPORTING

Judge the final report.

Consider:

• Covers requested analysis

• Includes important findings

• References generated charts where appropriate

• Uses execution results

5 = Excellent

1 = Poor


OVERALL

Overall quality of the complete workflow from user query to final report.

Provide a score from 1-5 for each metric together with concise reasoning.
"""
    )

    chain = prompt | judge

    try:

        result = chain.invoke(
            {
                "user_query": user_query,

                "expected_route": expected["expected_route"],
                "expected_plan_keywords": expected["expected_plan_keywords"],
                "expected_execution_status": expected["expected_execution_status"],
                "expected_chart_count": expected["expected_chart_count"],
                "expected_chart_types": expected["expected_chart_types"],
                "expected_report_keywords": expected["expected_report_keywords"],
                "expected_critic_verdict": expected["expected_critic_verdict"],
                "expected_retry_count": expected["expected_retry_count"],
                "expected_final_supervisor_decision": expected["expected_final_supervisor_decision"],

                "conversation_route": outputs.get("conversation_route", ""),
                "supervisor_decision": outputs.get("supervisor_decision", ""),
                "plan": outputs.get("plan", ""),
                "execution_status": outputs.get("execution_status", ""),
                "execution_error": outputs.get("execution_error", ""),
                "chart_files": outputs.get("chart_files", []),
                "critic_verdict": outputs.get("critic_verdict", ""),
                "retry_count": outputs.get("retry_count", 0),
                "final_report": outputs.get("final_report", ""),
            }
        )

        return [
            {
                "key": "Routing_Score",
                "score": result.routing,
                "comment": result.routing_reason,
            },
            {
                "key": "Planning_Score",
                "score": result.planning,
                "comment": result.planning_reason,
            },
            {
                "key": "Execution_Score",
                "score": result.execution,
                "comment": result.execution_reason,
            },
            {
                "key": "Reporting_Score",
                "score": result.reporting,
                "comment": result.reporting_reason,
            },
            {
                "key": "Overall_Score",
                "score": result.overall,
                "comment": result.overall_reason,
            },
        ]

    except Exception as e:

        return [
            {
                "key": "Routing_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Planning_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Execution_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Reporting_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Overall_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
        ]