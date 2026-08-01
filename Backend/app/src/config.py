from langchain_groq import ChatGroq

# ==========================================================
# STRICT Per-request LLM factory
# ==========================================================

def get_llm(api_key: str, model: str | None = None, max_retries: int | None = None) -> ChatGroq:
    """
    Create a ChatGroq instance strictly using the user-provided parameters.
    No environment variable fallbacks are used.
    """
    if not api_key:
        raise ValueError("A valid Groq API key must be provided by the user.")
        
    mdl = model or "llama-3.3-70b-versatile"

    kwargs: dict = {
        "model": mdl,
        "temperature": 0.1,
        "api_key": api_key,
        "streaming": True, #  ADDED THIS! Now the LLM will stream tokens!
    }

    if max_retries is not None:
        kwargs["max_retries"] = max_retries

    return ChatGroq(**kwargs)