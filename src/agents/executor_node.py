from src.graph.state import GraphState
import sys
import io
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from data_frame import global_df

def executor_node(state: GraphState):
    """Executes the code securely with injected tools and persists data modifications."""
    print("⚙️ Executor is running the code...")
    code = state["current_code"]
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    error_msg = None
    plt.switch_backend('Agg') 
    
    # Expose global_df and other safe utilities to the execution environment
    exec_globals = {
        "global_df": global_df,          # Base dataframe
        "plt": plt,
        "sns": sns,
        "pd": pd,
        "pl": pl
    }
    
    try:
        exec(code, exec_globals)
        
        # Persist any data cleaning or modifications back to the global scope
        if "global_df" in exec_globals:
            import data_frame
            data_frame.global_df = exec_globals["global_df"]
            
    except Exception as e:
        error_msg = str(e)
    finally:
        sys.stdout = old_stdout
        
    if error_msg:
        return {"execution_output": error_msg, "has_error": True}
    else:
        return {"execution_output": redirected_output.getvalue(), "has_error": False}