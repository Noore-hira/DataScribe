import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from evaluators.programmer_evaluators import evaluate_code_metrics

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
def run_programmer(inputs: dict) -> dict:
    """
    Actively executes your Programmer node.
    LangSmith will trace this execution to capture latency and token usage.
    """
    time.sleep(5)
    user_query = inputs.get("user_query", "")
    df_schema = inputs.get("df_schema", "")
    plan = inputs.get("plan", "")
    
    # Construct the state dictionary exactly as your LangGraph expects it
    state = {
        "user_query": user_query,
        "df_schema": df_schema,
        "plan": plan,
        "messages": [],
        "model": "llama-3.3-70b-versatile", # Required by your get_llm function
        "supervisor_feedback": "",
        "code": "" # Or "generated_code", depending on your state schema
    }
    
    # Extract API key for the node
    api_key = os.environ.get("GROQ_API_KEY") 
    
    # Create the mock config that your node requires
    mock_config = {
        "configurable": {
            "thread_id": "eval_run",
            "api_key": api_key
        }
    }
    
    try:
        # Import and execute the Programmer node
        from Backend.app.src.agents.programmer_node import programmer_node
        
        # Pass BOTH state and config to the node
        result_state = programmer_node(state, mock_config)
        
        # Depending on your exact state schema, it might be saved under "code" or "generated_code"
        generated_code = result_state.get("code", result_state.get("generated_code", ""))
        
    except Exception as e:
        generated_code = f"Node Execution Failed: {str(e)}"
    
    return {"generated_code": generated_code}


# =============
# 3. Execution 
# =============
if __name__ == "__main__":
    print("Starting Programmer 1-5 Scale Evaluation...")
    
    # NOTE: Ensure your dataset in LangSmith is actually named "Programmer Evaluation"
    experiment_results = evaluate(
        run_programmer, 
        data="Programmer Evaluation", 
        evaluators=[evaluate_code_metrics], 
        experiment_prefix="programmer-online-metrics"
    )
    
    print("Evaluation complete!")
