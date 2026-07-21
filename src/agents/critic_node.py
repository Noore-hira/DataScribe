from src.config import llm
from src.graph.state import GraphState
from pydantic import BaseModel, Field
from typing import Literal

class CriticVerdict(BaseModel):
    verdict: Literal["pass", "fail"] = Field(
        description="Pass if the code executed successfully and answered the plan. Fail if there are runtime errors or bad outputs."
    )
    critique: str = Field(description="Explanation of review results.")

def critic_node(state: GraphState):
    """Evaluates code execution output against quality standards."""
    print("------ CRITIC NODE ------")
    print("🔍 Critic is reviewing execution output...")
    
    if state.get("has_error", False):
        return {
            "has_error": True,
            "execution_output": f"CRITIC FEEDBACK: Code crashed with error:\n{state['execution_output']}"
        }
    
    return {"has_error": False}