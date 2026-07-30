"""
Lightweight validator for LLM-generated analysis code.

E2B Sandbox provides the security isolation.
This module only enforces analysis workflow rules:
- valid Python syntax
- prevent unsupported code patterns
- normalize visualization outputs
- keep artifacts inside run directory
"""

from __future__ import annotations

import ast
import os


class UnsafeCodeError(ValueError):
    def __init__(
        self,
        category: str,
        message: str,
        suggestion: str,
    ):
        self.category = category
        self.suggestion = suggestion
        super().__init__(message)


# Blocked patterns for agent-generated analysis code
_BLOCKED_NODES = (
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.Global,
    ast.Nonlocal,
)


_ALLOWED_OUTPUT_METHODS = {
    "savefig",
    "write_html",
    "write_image",
}


def validate_analysis_code(
    code: str,
    *,
    artifact_dir: str | None = None,
) -> ast.Module:
    """
    Validate generated dataframe analysis code.

    E2B handles security.
    This only enforces agent behavior.
    """

    try:
        tree = ast.parse(code, mode="exec")

    except SyntaxError as e:
        raise UnsafeCodeError(
            "syntax_error",
            str(e),
            "Generate valid Python code."
        )

    for node in ast.walk(tree):

        # Avoid private Python internals
        if isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise UnsafeCodeError(
                    "private_access",
                    f"Private name blocked: {node.id}",
                    "Do not access Python internals."
                )


        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise UnsafeCodeError(
                    "private_access",
                    f"Private attribute blocked: {node.attr}",
                    "Avoid dunder attributes."
                )


        # Keep generated code simple
        if isinstance(node, _BLOCKED_NODES):
            raise UnsafeCodeError(
                "unsupported_structure",
                f"Unsupported syntax: {type(node).__name__}",
                "Write sequential pandas analysis code."
            )


        # Ensure visualization files have names
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _ALLOWED_OUTPUT_METHODS
        ):

            if artifact_dir is None:
                raise UnsafeCodeError(
                    "artifact_missing",
                    "Artifact directory not provided.",
                    "Save visualizations through the executor."
                )

            if not node.args:
                raise UnsafeCodeError(
                    "missing_filename",
                    "Visualization filename missing.",
                    "Provide an output filename."
                )

    return tree



def normalize_visualization_artifacts(
    code: str,
    artifact_dir: str,
) -> str:
    """
    Redirect all generated charts/reports
    into the current E2B run artifact folder.
    """

    tree = ast.parse(code, mode="exec")

    artifact_dir = os.path.normpath(
        artifact_dir
    ).replace("\\", "/")


    class Rewriter(ast.NodeTransformer):

        def __init__(self):
            self.counter = 0


        def visit_Call(self, node):

            self.generic_visit(node)

            if not isinstance(node.func, ast.Attribute):
                return node


            method = node.func.attr


            if method not in {
                "savefig",
                "write_html",
                "write_image",
            }:
                return node


            self.counter += 1


            ext = {
                "savefig": "png",
                "write_html": "html",
                "write_image": "png",
            }[method]


            filename = os.path.join(
                artifact_dir,
                f"chart_{self.counter}.{ext}"
            ).replace("\\", "/")


            if node.args:
                node.args[0] = ast.Constant(filename)
            else:
                node.args.append(
                    ast.Constant(filename)
                )

            return node


    tree = Rewriter().visit(tree)

    ast.fix_missing_locations(tree)

    return ast.unparse(tree)