from src.config import llm
from src.graph.state import GraphState
from langchain_core.messages import SystemMessage,HumanMessage
from pydantic import BaseModel, Field

class SupervisorDecision(BaseModel):
    decision: str = Field(
        description="Must be one of: "
                    "'profile' (if user asks a generic query like 'tell me about the data' or 'summarize everything'), "
                    "'analyze' (if user asks a specific question requiring data manipulation), "
                    "'approve' (if the final_report perfectly answers the original query), "
                    "'rework' (if final_report exists but fails to answer the user query completely)."
    )
    plan_or_feedback: str = Field(
        description="If 'analyze', write a step-by-step coding plan. "
                    "If 'rework', write feedback explaining why the report failed and what the programmer should do differently. "
                    "If 'approve' or 'profile', leave empty."
    )

def supervisor_node(state: GraphState):
    """Acts as the router and final QA judge with a strict circuit breaker."""
    print("👔 Supervisor is reviewing the state...")
    
    # CIRCUIT BREAKER: Stop infinite loops
    current_revisions = state.get("revision_count", 0)
    if current_revisions >= 2:
        print("🛑 Maximum reworks reached. Forcing completion.")
        return {
            "supervisor_decision": "approve", 
            "plan": "Max revisions reached.",
            "revision_count": current_revisions
        }
    
    structured_llm = llm.with_structured_output(SupervisorDecision)
    
    report_context = ""
    if state.get("final_report"):
        report_context = f"\n\nCURRENT FINAL REPORT:\n{state['final_report']}\nDoes this completely answer the user query?"

    sys_prompt = (
        "You are a Principal Data Scientist orchestrating an AI data team. "
        "Review the user query, schema, and current report (if it exists). "
        "Output your routing decision and plan in strict JSON."
        "If the user requests charts or plots, your plan MUST explicitly instruct the Programmer to call the create_visualization_tool."
    )
    
    user_content = f"Query: {state['user_query']}\nSchema:\n{state['df_schema']}{report_context}"
    
    response = structured_llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_content)
    ])
    
    # Increment the revision count if the decision is a rework
    next_revision_count = current_revisions + 1 if response.decision == "rework" else current_revisions
    
    return {
        "supervisor_decision": response.decision,
        "plan": response.plan_or_feedback,
        "revision_count": next_revision_count
    }