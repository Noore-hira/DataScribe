from pydantic import BaseModel, Field
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()
# ==========================================
# Programmer Judge Schema
# ==========================================

class ProgrammerEvaluation(BaseModel):
    correctness: int = Field(..., ge=1, le=5)
    executability: int = Field(..., ge=1, le=5)

    correctness_reason: str
    executability_reason: str


judge_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
)

judge = judge_llm.with_structured_output(ProgrammerEvaluation)

# ==========================================
# 2. 1-5 Scale Multi-Metric Evaluator
# ==========================================
def evaluate_code_metrics(run, example) -> list[dict]:
    """
    Evaluates Correctness and Executability of Python code on a 1-5 scale.
    """
    expected_code = example.outputs["expected_code"]
    user_query = example.inputs["user_query"]
    
    # Safely extract the code in case the execution fails
    outputs = run.outputs or {}
    generated_code = outputs.get("generated_code", "Error: No code generated.")
    
    # If the node failed, immediately return 1s (completely incorrect/unexecutable)
    if "Node Execution Failed" in generated_code or "Error:" in generated_code:
        return [
            {"key": "Correctness_Score", "score": 1, "comment": generated_code},
            {"key": "Executability_Score", "score": 1, "comment": generated_code}
        ]
    
    prompt = PromptTemplate.from_template("""
    You are an impartial evaluator of AI-generated Python code.

    Evaluate ONLY the generated Python code.

    The Expected Reference Code is ONE valid implementation.
    The Generated Code does NOT need to match it exactly.

    Reward alternative implementations that produce the same correct result.

    Ignore:
    - variable names
    - formatting
    - comments
    - ordering of independent operations

    Evaluate using TWO metrics only.

    USER REQUEST
    ------------
    {user_query}

    REFERENCE CODE
    --------------
    {expected_code}

    GENERATED CODE
    --------------
    {generated_code}

    CORRECTNESS

    Judge whether the generated code correctly solves the user's request.

    Consider:
    - correct analysis
    - correct calculations
    - correct statistics
    - correct visualizations
    - appropriate dataframe operations
    - logically correct workflow

    5 = Completely correct
    4 = Minor issues
    3 = Partially correct
    2 = Major analytical mistakes
    1 = Incorrect solution

    EXECUTABILITY

    Judge whether the code would execute successfully in the provided environment.

    Consider:
    - valid Python syntax
    - correct indentation
    - defined variables
    - valid dataframe operations
    - required column checks
    - no obvious runtime errors
    - charts saved correctly
    - compatible with the execution environment

    Ignore code style.

    5 = Executes successfully
    4 = Minor issue
    3 = One runtime issue
    2 = Multiple runtime issues
    1 = Cannot execute

    Provide scores from 1-5 for both metrics and concise reasoning for each.
    """)
    
    chain = prompt | judge
    
    try:
        result = chain.invoke(
            {
                "user_query": user_query,
                "expected_code": expected_code,
                "generated_code": generated_code,
            }
        )

        return [
            {
                "key": "Correctness_Score",
                "score": result.correctness,
                "comment": result.correctness_reason,
            },
            {
                "key": "Executability_Score",
                "score": result.executability,
                "comment": result.executability_reason,
            }
        ]
        
    except Exception as e:
        return [
            {
                "key": "Correctness_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            },
            {
                "key": "Executability_Score",
                "score": 1,
                "comment": f"Judge Error: {e}",
            }
        ]
