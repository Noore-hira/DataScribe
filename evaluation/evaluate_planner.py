import os
import sys
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from evaluators.planner_evaluators import evaluate_plan_metrics

# Setup path so Python can find the 'Backend' module
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()
# Initialize LangSmith Client
client = Client()


# ==========================================
# 1. Active Target Function (Tracks Latency)
# ==========================================
def run_planner(inputs: dict) -> dict:
    """
    Actively executes your Planner node.
    LangSmith will trace this execution to capture latency and token usage.
    """
    user_query = inputs.get("user_query", "")
    df_schema = inputs.get("df_schema", "")
    
    # Construct the state dictionary exactly as your LangGraph expects it
    state = {
        "user_query": user_query,
        "df_schema": df_schema,
        "messages": [],
        "model": "llama-3.3-70b-versatile", # Required by your get_llm function
        "supervisor_feedback": "",
        "plan": ""
    }
    
    # Extract API key for the node
    api_key = os.environ.get("GROQ_API_KEY") 
    
    # 🛠️ Create the mock config that your node requires
    mock_config = {
        "configurable": {
            "thread_id": "eval_run",
            "api_key": api_key
        }
    }
    
    try:
        # Import and execute the node
        from Backend.app.src.agents.planner_node import planner_node
        
        # 🛠️ Pass BOTH state and config to the node
        result_state = planner_node(state, mock_config)
        generated_plan = result_state.get("plan", "")
        
    except Exception as e:
        generated_plan = f"Node Execution Failed: {str(e)}"
    
    return {"generated_plan": generated_plan}



# ==========================================
# 3. Execution 
# ==========================================
if __name__ == "__main__":
    print("Starting Active 1-5 Scale Evaluation...")
    
    experiment_results = evaluate(
        run_planner, 
        data="Planner Evaluation", 
        evaluators=[evaluate_plan_metrics], 
        experiment_prefix="online-metrics-run"
    )
    
    print("Evaluation complete!")