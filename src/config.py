import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


# ==========================================================
# Default LLM instances (backward compatibility)
# ==========================================================

_default_api_key = os.getenv("GROQ_API")

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.1, api_key=_default_api_key)
llm_for_pg = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=_default_api_key, max_retries=2)


# ==========================================================
# Per-request LLM factory
# ==========================================================

def get_llm(api_key: str | None = None, model: str | None = None, max_retries: int | None = None) -> ChatGroq:
    """
    Create a ChatGroq instance with the given parameters.

    Falls back to environment variables when ``api_key`` or ``model``
    are not provided, so the backend works even if the frontend does
    not send them.
    """
    key = api_key or os.getenv("GROQ_API")
    mdl = model or "openai/gpt-oss-20b"

    kwargs: dict = {
        "model": mdl,
        "temperature": 0.1,
        "api_key": key,
    }

    if max_retries is not None:
        kwargs["max_retries"] = max_retries

    return ChatGroq(**kwargs)
