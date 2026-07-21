from src.config import llm
from src.graph.state import GraphState
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from data_frame import global_df
import io

class SupervisorDecision(BaseModel):
    decision: Literal["planner", "programmer", "designer", "reporter", "end", "rework"] = Field(
        description="The next node to execute based on progress. "
                    "Sequence: planner -> programmer -> designer -> reporter -> end."
    )
    plan_or_feedback: str = Field(
        description="Provide instructions or feedback for the next node."
    )

def programmer_node(state: GraphState):
    """Data scientist agent writes code based on the plan and schema."""
    print("💻 Data Scientist is writing Pandas analysis and cleaning code...")
    
    # Safely retrieve state properties to avoid KeyErrors
    plan = state.get("plan", "No plan provided.")
    df_schema = state.get("df_schema", "Schema not available.")
    execution_output = state.get("execution_output", "")
    has_error = state.get("has_error", False)
    
    error_context = ""
    if has_error and execution_output:
        error_context = f"\n\nPrevious execution failed with this output/error:\n{execution_output}\nPlease fix the code."

    prompt = f"Plan: {plan}\nSchema:\n{df_schema}{error_context}"
    
    # ... rest of your programmer node execution logic

    # Auto-initialize missing fields (like when starting from LangGraph Studio)
    if not df_schema:
        print("🔄 Auto-generating dataset schema for incoming run...")
        buffer = io.StringIO()
        global_df.info(buf=buffer)
        df_schema = buffer.getvalue()
        
        retry_count = 0
        revision_count = 0
        charts_completed = False
        execution_output = ""
        plan = "Initial plan formulation"
    
    if revision_count >= 2:
        print("🛑 Maximum reworks reached. Forcing completion.")
        return {
            "df_schema": df_schema,
            "supervisor_decision": "end", 
            "plan": "Max revisions reached.",
            "revision_count": revision_count,
            "retry_count": retry_count,
            "charts_completed": charts_completed,
            "execution_output": execution_output
        }
    
    structured_llm = llm.with_structured_output(SupervisorDecision)
    
    has_execution_output = bool(execution_output)
    has_report = bool(state.get("final_report", ""))
    user_query = state.get("user_query", "")
    
    user_query_lower = user_query.lower()
    needs_charts = any(kw in user_query_lower for kw in ["chart", "plot", "donut", "bar", "graph", "visual"])
    
    sys_prompt = (
        "You are the Lead Project Supervisor of an AI data science team.\n"
        "STRICT PIPELINE & STATE RULES:\n"
        "1. If there is no active plan, route to 'planner'.\n"
        "2. If data cleaning/analysis has not run yet (check execution output), route to 'programmer'.\n"
        "3. If charts/plots were requested AND `charts_completed` is False, you MUST route to 'designer'. "
        "Do NOT route to programmer or rework if data cleaning is already done and charts are just pending.\n"
        "4. If technical work and charts are done, but no final report exists (or report lacks data), route to 'reporter'.\n"
        "5. If a final report exists and includes the necessary insights/charts, route to 'end'. "
        "Only route to 'rework' if the report contains errors or misses critical user requirements, and keep revisions strictly under 2."
    )
    
    user_content = (
        f"User Query: {user_query}\n"
        f"Current Plan: {plan}\n"
        f"Has Execution Output (Cleaning Done): {has_execution_output}\n"
        f"Charts Completed Flag: {charts_completed}\n"
        f"Has Final Report: {has_report}\n"
        f"Dataset Schema:\n{df_schema}"
    )
    
    response: SupervisorDecision = structured_llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_content)
    ])
    
    decision = response.decision
    
    # SAFETY INTERCEPTS TO PREVENT LOOPS:
    if decision == "designer" and charts_completed:
        decision = "reporter"
    elif decision == "rework" and not charts_completed and needs_charts:
        print("⚠️ Supervisor attempted rework for missing charts. Forcing route to DESIGNER.")
        decision = "designer"
        
    print(f"👔 LLM Routing Decision -> {decision.upper()} ({response.plan_or_feedback})")
    
    next_revision_count = revision_count + 1 if decision == "rework" else revision_count
    
    # Explicitly return all tracking variables so LangGraph maintains state integrity
    return {
        "df_schema": df_schema,
        "supervisor_decision": decision,
        "plan": response.plan_or_feedback,
        "revision_count": next_revision_count,
        "retry_count": retry_count,
        "charts_completed": charts_completed,
        "execution_output": execution_output
    }