import re
from src.config import llm_for_pg
from src.graph.state import GraphState

programmer_instructions = (
    "You are a specialized Data Scientist. Your ONLY job is to write pure Pandas Python code.\n"
    "CRITICAL RULES:\n"
    "1. You have NO tools. Do not attempt to call any tools.\n"
    "2. The dataset is already loaded in memory as `global_df`.\n"
    "3. MANDATORY CLEANING STEP: Before performing any analysis or calculations, your code MUST automatically clean the data first (e.g., handle missing values by filling numerical columns with the median and categorical columns with 'Unknown', and parse dates correctly)[cite: 1].\n"
    "4. You MUST use `print()` statements to output your statistical calculations so they appear in stdout.\n"
    "5. Wrap your final Python code strictly inside ```python ... ``` blocks."
)

def programmer_node(state: GraphState):
    """Data Scientist node writes clean data analysis code with built-in cleaning."""
    print("💻 Data Scientist is writing Pandas analysis and cleaning code...")
    
    error_context = f"\n\nPREVIOUS CODE FAILED:\n{state['execution_output']}" if state.get("has_error") else ""
    prompt = f"Plan: {state['plan']}\nSchema:\n{state['df_schema']}{error_context}"
    
    response = llm_for_pg.invoke([
        {"role": "system", "content": programmer_instructions},
        {"role": "user", "content": prompt}
    ])
    
    raw_output = response.content
    code_match = re.search(r"```python\n(.*?)\n```", raw_output, re.DOTALL)
    code = code_match.group(1) if code_match else "print('No code block generated.')"
    
    return {"current_code": code}