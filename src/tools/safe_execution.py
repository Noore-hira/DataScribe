"""
Small guardrail for model-produced analysis code.

This is NOT a security sandbox. It blocks common unsafe operations and
rewrites visualization output paths. Generated code should still be executed
inside a sandboxed worker in production.
"""

from __future__ import annotations

import ast
import os


class UnsafeCodeError(ValueError):
    """Raised when generated code violates execution rules."""


# ---------------------------------------------------------------------
# Unsafe operations
# ---------------------------------------------------------------------

_BANNED_NAMES = {
    "open",
    "exec",
    "eval",
    "compile",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
}

_BANNED_ATTRIBUTES = {
    "read_csv",
    "read_excel",
    "read_json",
    "read_parquet",
    "to_csv",
    "to_excel",
    "to_pickle",
    "to_sql",
    "system",
    "popen",
    "remove",
    "unlink",
    "rmtree",
}

_BANNED_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.AsyncWith,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.Global,
    ast.Nonlocal,
)


# ---------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------


def validate_analysis_code(
    code: str,
    *,
    artifact_dir: str | None = None,
) -> ast.Module:
    """
    Validate generated Python code.

    If artifact_dir is supplied, Plotly/Matplotlib save operations
    are allowed ONLY inside that directory.
    """

    tree = ast.parse(code, mode="exec")

    normalized_artifact_dir = None

    if artifact_dir:
        normalized_artifact_dir = (
            os.path.normpath(artifact_dir)
            .replace("\\", "/")
            .rstrip("/")
        )

    for node in ast.walk(tree):

        # ----------------------------------------------------------
        # Unsupported statements
        # ----------------------------------------------------------

        if isinstance(node, _BANNED_NODES):
            raise UnsafeCodeError(
                f"Unsupported statement: {type(node).__name__}"
            )

        # ----------------------------------------------------------
        # Unsafe names
        # ----------------------------------------------------------

        if isinstance(node, ast.Name):

            if (
                node.id.startswith("__")
                or node.id in _BANNED_NAMES
            ):
                raise UnsafeCodeError(
                    f"Unsafe name: {node.id}"
                )

        # ----------------------------------------------------------
        # Unsafe attributes
        # ----------------------------------------------------------

        if isinstance(node, ast.Attribute):

            if (
                node.attr.startswith("__")
                or node.attr in _BANNED_ATTRIBUTES
            ):
                raise UnsafeCodeError(
                    f"Unsafe attribute: {node.attr}"
                )

        # ----------------------------------------------------------
        # Validate visualization save paths
        # ----------------------------------------------------------

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"write_html", "savefig"}
        ):

            if artifact_dir is None:
                raise UnsafeCodeError(
                    "Visualization output is not allowed."
                )

            if not node.args:
                raise UnsafeCodeError(
                    "Visualization must provide an output filename."
                )

            if (
                not isinstance(node.args[0], ast.Constant)
                or not isinstance(node.args[0].value, str)
            ):
                raise UnsafeCodeError(
                    "Visualization output path must be a string literal."
                )

            output_path = (
                os.path.normpath(node.args[0].value)
                .replace("\\", "/")
            )

            if not output_path.startswith(
                normalized_artifact_dir + "/"
            ):
                raise UnsafeCodeError(
                    "Chart files must be saved in the run artifact directory."
                )

    return tree


# ---------------------------------------------------------------------
# Safe builtins
# ---------------------------------------------------------------------

SAFE_BUILTINS = {
    "print": print,
    "len": len,
    "round": round,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
}


# ---------------------------------------------------------------------
# Visualization path normalizer
# ---------------------------------------------------------------------


def normalize_visualization_artifacts(
    code: str,
    artifact_dir: str,
) -> str:
    """
    Rewrites every:

        fig.write_html(...)
        plt.savefig(...)

    so that files are always saved into the current run's
    artifact directory.

    This prevents the LLM from writing outside the workspace.
    """

    tree = ast.parse(code, mode="exec")

    artifact_dir = os.path.normpath(artifact_dir)

    class ArtifactRewriter(ast.NodeTransformer):

        def __init__(self):
            self.counter = 0

        def visit_Call(self, node):

            self.generic_visit(node)

            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {
                    "write_html",
                    "savefig",
                }
            ):

                self.counter += 1

                extension = (
                    "html"
                    if node.func.attr == "write_html"
                    else "png"
                )

                filename = os.path.join(
                    artifact_dir,
                    f"chart_{self.counter}.{extension}",
                )

                filename = filename.replace("\\", "/")

                literal = ast.Constant(
                    value=filename
                )

                if node.args:
                    node.args[0] = literal
                else:
                    node.args.append(literal)

            return node

    tree = ArtifactRewriter().visit(tree)

    ast.fix_missing_locations(tree)

    return ast.unparse(tree)