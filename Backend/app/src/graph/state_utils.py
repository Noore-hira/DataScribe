from typing import Any

from Backend.app.src.graph.state import GraphState


class StateValidationError(ValueError):
    """Raised when a required state field is missing."""


def require_state(state: GraphState, key: str) -> Any:
    """
    Return a required state value.

    Raises a descriptive exception if the value is missing.
    """

    value = state.get(key)

    if value is None:
        raise StateValidationError(
            f"Required state field '{key}' is missing."
        )

    return value


def get_state(
    state: GraphState,
    key: str,
    default: Any = None,
) -> Any:
    """
    Safe wrapper around state.get().
    """

    return state.get(key, default)