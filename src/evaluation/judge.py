import json

from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

from langchain_core.messages import HumanMessage, SystemMessage

from src.config import llm


JSON_INSTRUCTIONS = """
Return ONLY valid JSON.

Schema:

{
    "score": integer (1-5),
    "reason": string
}

Rules:

- No markdown
- No explanations
- No code fences
- No additional keys
- score must be an integer from 1 to 5
- reason must be a short sentence

Return ONLY the JSON object.
"""


class Evaluation(BaseModel):
    score: int = Field(
        ge=1,
        le=5,
    )

    reason: str


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
)
def judge(
    system_prompt: str,
    user_prompt: str,
) -> Evaluation:

    response = llm.invoke(
        [
            SystemMessage(
                content=system_prompt
                + "\n\n"
                + JSON_INSTRUCTIONS
            ),
            HumanMessage(content=user_prompt),
        ]
    )

    text = response.content.strip()

    # Sometimes models wrap JSON inside ```json
    if text.startswith("```"):

        text = (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    try:

        return Evaluation.model_validate(
            json.loads(text)
        )

    except Exception as e:

        print("\nFailed evaluation output:\n")
        print(text)

        raise e