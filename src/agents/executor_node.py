from src.graph.state import GraphState
import sys
import io
import re
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from data_frame import load_dataframe
from src.tools.safe_execution import SAFE_BUILTINS, validate_analysis_code

def executor_node(state: GraphState):
    """Executes the code securely with injected tools and persists data modifications."""
    print("Executor is running the code...")
    if state.get("fatal_error"):
        return {"has_error": True, "execution_output": state["fatal_error"]}

    code = state.get("current_code", "")
    # Imports are unnecessary because the permitted analysis libraries are
    # injected below. Remove a model's redundant import lines before applying
    # the AST safety policy.
    code = re.sub(r"^\s*(?:from\s+\S+\s+import\s+.+|import\s+.+)\s*$", "", code, flags=re.MULTILINE)
    code = re.sub(r"^\s*plt\.show\(\)\s*$", "", code, flags=re.MULTILINE)
    if not code:
        return {"has_error": True, "execution_output": "No analysis code was generated."}
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    error_msg = None
    plt.switch_backend('Agg') 
    
    # Each run receives a fresh dataset. Generated code has no filesystem or
    # process access and is validated before execution.
    exec_globals = {
        "__builtins__": SAFE_BUILTINS,
        "global_df": load_dataframe(),
        "plt": plt,
        "sns": sns,
        "pd": pd,
        "pl": pl
    }
    
    try:
        exec(compile(validate_analysis_code(code), "<generated-analysis>", "exec"), exec_globals)
    except Exception as e:
        error_msg = str(e)
    finally:
        sys.stdout = old_stdout
        
    if error_msg:
        return {
            "execution_output": error_msg,
            "has_error": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }
    else:
        return {"execution_output": redirected_output.getvalue(), "has_error": False}
