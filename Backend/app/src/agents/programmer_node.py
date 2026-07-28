from langchain_core.messages import HumanMessage, SystemMessage

from Backend.app.src.config import get_llm
from Backend.app.src.graph.state import GraphState
from Backend.app.src.logs.logger import logger
from Backend.app.src.utils.code_executor import extract_python_code
from langsmith import Client
from dotenv import load_dotenv

load_dotenv()
client = Client()

SYSTEM_PROMPT = client.pull_prompt("programmer_sp").format()
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

    response = get_llm(state.get("api_key"), "openai/gpt-oss-120b" , max_retries=2).invoke(
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
        "programmer_metrics": {

            "lines": len(code.splitlines()),
            "characters": len(code)
            }
    }