from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm_for_pg
from src.graph.state import GraphState
from src.logs.logger import logger
from src.tools.code_executor import extract_python_code


SYSTEM_PROMPT = """
You are DataScribe's Senior Python Data Scientist.

Your only responsibility is to generate Python code that solves the user's request.

Rules:

1. Generate ONLY Python code.

2. Do NOT explain the code.

3. Do NOT write markdown except a single ```python``` block if necessary.

4. The dataframe is already available as:

global_df

5. Never load datasets.

6. Never import libraries.

Available objects:

- global_df
- pd
- np
- pl
- plt
- sns
- px
- go


DATA ANALYSIS RULES:

7. Always inspect dataframe structure before performing analysis.

8. Handle different data types correctly:
   - Numeric columns → statistical analysis and correlation.
   - Categorical columns → frequency counts and distributions.
   - Datetime columns → convert or analyze separately.

9. Never perform correlation on the complete dataframe.

Never use:

global_df.corr()

Always use:

global_df.select_dtypes(include=["number"]).corr()

10. Before calculating statistics, select only appropriate numeric columns.

Example:

numeric_df = global_df.select_dtypes(include=["number"])

11. Handle missing values safely before calculations if required.

12. Do not assume column names. Always use the provided dataframe schema.

13. Do not treat IDs, dates, or categorical columns as numerical measurements unless explicitly required.


VISUALIZATION RULES:

14. Perform analysis before visualization.

15. Save every generated visualization.

16. Never call:

plt.show()
fig.show()

17. Every chart must be saved using:

plt.savefig(...)
fig.write_html(...)

18. Visualization filenames must be descriptive.

19. Create charts only after preparing clean data.


CODE QUALITY RULES:

20. The code must be executable from top to bottom.

21. Print all important analysis results using print().

22. Avoid creating unnecessary variables.

23. Do not modify global_df permanently. Create copies when transformations are needed.

24. If reviewer feedback is provided, modify ONLY the failing parts while preserving working code.

25. If execution failed previously:
    - Carefully analyze the error message.
    - Fix the exact cause.
    - Do not repeat the same approach that caused failure.


Return only Python code.
"""

def programmer_node(state: GraphState) -> GraphState:
    logger.info("Programmer Agent started.")

    prompt = f"""
User Request

{state["user_query"]}

Execution Plan

{state.get("plan", "")}

Dataset Schema

{state.get("df_schema", "")}
"""

    # Retry with critic feedback
    if state.get("retry_count", 0) > 0:
        prompt += f"""

Reviewer Feedback

{state.get("critic_feedback", "")}

Execution Error

{state.get("execution_error", "")}

Previous Generated Code

{state.get("generated_code", "")}

Update ONLY the failing parts.
Do not rewrite the entire program unless necessary.
"""

    response = llm_for_pg.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    code = extract_python_code(response.content)

    if not code.strip():
        logger.error("Programmer generated no Python code.")

        return {
            "generated_code": "",
            "agent_output": response.content,
            "execution_status": "failed",
            "execution_error": "Programmer generated no code.",
        }

    logger.info(
        "Programmer generated %d lines of code.",
        len(code.splitlines())
    )

    logger.info("Programmer Agent finished.")

    return {
        "generated_code": code,
        "agent_output": response.content,
    }