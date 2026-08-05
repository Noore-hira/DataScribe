import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()

# ==========================================
# Planner Judge
# ==========================================

class PlannerEvaluation(BaseModel):
    correctness: int = Field(..., ge=1, le=5)
    completeness: int = Field(..., ge=1, le=5)
    relevance: int = Field(..., ge=1, le=5)

    correctness_reason: str
    completeness_reason: str
    relevance_reason: str


judge_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
)

judge = judge_llm.with_structured_output(PlannerEvaluation)

#1-5 Scale Multi-Metric Evaluator

def evaluate_plan_metrics(run, example) -> list[dict]:
    """
    Evaluates Correctness, Completeness, and Relevance on a 1-5 scale.
    """
    expected_plan = example.outputs["expected_plan"]
    user_query = example.inputs["user_query"]
    
    # 🛠️ Safely extract the plan in case the execution fails
    outputs = run.outputs or {}
    generated_plan = outputs.get("generated_plan", "Error: No plan generated.")
    
    # If the node failed, immediately return 1s (completely incorrect/missing)
    if "Node Execution Failed" in generated_plan or "Error:" in generated_plan:
        return [
            {"key": "Correctness_Score", "score": 1, "comment": generated_plan},
            {"key": "Completeness_Score", "score": 1, "comment": generated_plan},
            {"key": "Relevance_Score", "score": 1, "comment": generated_plan}
        ]
    
    prompt = PromptTemplate.from_template("""
    You are an impartial evaluator of AI-generated data analysis plans.

    Your task is to evaluate ONLY the planning quality.

    Do NOT evaluate implementation, Python code quality, syntax, execution, or formatting.

    The Expected Reference Plan is ONE valid solution.
    The Generated Plan does NOT need to match its wording, ordering, or formatting.

    Judge based on whether the Generated Plan would successfully solve the user's request.

    Reward semantic equivalence rather than textual similarity.

    Ignore:
    - wording differences
    - numbering differences
    - bullet formatting
    - ordering of valid steps
    - different but equally valid analytical approaches

    Penalize:
    - incorrect analytical reasoning
    - logically inconsistent workflows
    - missing essential analysis steps
    - irrelevant analysis
    - hallucinated tasks
    - technically incorrect operations

    User Query
    -----------
    {user_query}

    Expected Reference Plan
    -----------------------
    {expected_plan}

    Generated Plan
    --------------
    {generated_plan}

    Evaluate the Generated Plan using the following rubrics.

    CORRECTNESS

    5
    All essential analytical steps are technically correct.
    No incorrect reasoning.

    4
    Minor inaccuracies that do not significantly affect the analysis.

    3
    Some correct planning, but at least one important analytical mistake.

    2
    Major analytical mistakes that would likely produce an incorrect analysis.

    1
    Fundamentally incorrect or unrelated plan.

    COMPLETENESS

    5
    Includes every important planning step required.

    4
    Missing one minor step.

    3
    Missing one important step.

    2
    Missing several important steps.

    1
    Most required planning steps are absent.

    RELEVANCE

    5
    Every task directly contributes to answering the user's request.

    4
    One minor unnecessary task.

    3
    Several unnecessary tasks.

    2
    Many irrelevant tasks.

    1
    Mostly unrelated to the user's request.

    Provide scores from 1-5 for each metric and concise reasoning for EACH metric separately.
    """)
    
    chain = prompt | judge
    
    try:
        result = chain.invoke(
            {
                "user_query": user_query,
                "expected_plan": expected_plan,
                "generated_plan": generated_plan,
            }
        )

        return [
            {
                "key": "Correctness_Score",
                "score": result.correctness,
                "comment": result.correctness_reason,
            },
            {
                "key": "Completeness_Score",
                "score": result.completeness,
                "comment": result.completeness_reason,
            },
            {
                "key": "Relevance_Score",
                "score": result.relevance,
                "comment": result.relevance_reason,
            },
        ]
        
    except Exception as e:
        return [
            {
                "key": "Correctness_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Completeness_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Relevance_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
        ]
