"""
Small guardrail for model-produced analysis code.

This is NOT a security sandbox.

Its purpose is to reject unsafe code before execution,
provide actionable feedback for retries,
and ensure visualization artifacts are saved only inside
the current run directory.
"""

from __future__ import annotations

import ast
import os


# ==========================================================
# Exception
# ==========================================================


class UnsafeCodeError(ValueError):
    """
    Raised when generated code violates execution rules.

    category
        Machine-readable error category.

    suggestion
        Actionable feedback that can be forwarded directly
        to the Critic / Programmer.
    """

    def __init__(
        self,
        category: str,
        message: str,
        suggestion: str,
    ):
        self.category = category
        self.suggestion = suggestion
        super().__init__(message)


# ==========================================================
# Unsafe operations
# ==========================================================

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
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "help",
    "breakpoint",
    "exit",
    "quit",
}


_BANNED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "pathlib",
    "shutil",
    "tempfile",
    "socket",
    "pickle",
    "joblib",
}


_BANNED_ATTRIBUTES = {

    # Pandas readers

    "read_csv",
    "read_excel",
    "read_json",
    "read_parquet",
    "read_sql",
    "read_pickle",

    # Writers

    "to_csv",
    "to_excel",
    "to_pickle",
    "to_sql",
    "to_parquet",

    # Filesystem

    "remove",
    "unlink",
    "rename",
    "replace",
    "mkdir",
    "makedirs",
    "rmdir",
    "rmtree",

    # Process

    "system",
    "popen",
    "run",

    # Serialization

    "dump",
    "load",

    # Network

    "get",
    "post",
    "request",
}


_BANNED_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.Global,
    ast.Nonlocal,
)


_ALLOWED_SAVE_METHODS = {
    "savefig",
    "write_html",
    "write_image",
}

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

    This is a guardrail, not a security sandbox.

    Allowed:
    - imports
    - helper functions
    - context managers
    - plotting
    - dataframe analysis

    Blocked:
    - dangerous builtins
    - dangerous filesystem/process APIs
    - writing files outside artifact directory
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
        # Unsupported syntax
        # ----------------------------------------------------------

        if isinstance(node, _BANNED_NODES):
            raise UnsafeCodeError(
                category="unsupported_syntax",
                message=f"Unsupported statement: {type(node).__name__}",
                suggestion=(
                    "Avoid unsupported Python syntax such as this statement. "
                    "Rewrite the code using standard sequential Python."
                ),
            )

        # ----------------------------------------------------------
        # Dangerous builtin names
        # ----------------------------------------------------------

        if isinstance(node, ast.Name):

            if node.id.startswith("__"):
                raise UnsafeCodeError(
                    category="unsafe_builtin",
                    message=f"Unsafe name: {node.id}",
                    suggestion=(
                        "Do not access Python dunder variables or special "
                        "builtins."
                    ),
                )

            if node.id in _BANNED_NAMES:
                raise UnsafeCodeError(
                    category="unsafe_builtin",
                    message=f"Unsafe builtin: {node.id}",
                    suggestion=(
                        f"Do not use '{node.id}'. Use the objects already "
                        "provided by the execution environment."
                    ),
                )

        # ----------------------------------------------------------
        # Dangerous attributes
        # ----------------------------------------------------------

        if isinstance(node, ast.Attribute):

            if node.attr.startswith("__"):
                raise UnsafeCodeError(
                    category="unsafe_attribute",
                    message=f"Unsafe attribute: {node.attr}",
                    suggestion=(
                        "Avoid accessing private or dunder attributes."
                    ),
                )

            if node.attr in _BANNED_ATTRIBUTES:
                raise UnsafeCodeError(
                    category="unsafe_attribute",
                    message=f"Unsafe attribute: {node.attr}",
                    suggestion=(
                        f"Do not call '{node.attr}'. "
                        "Use only safe dataframe analysis and visualization APIs."
                    ),
                )

        # ----------------------------------------------------------
        # Validate write_html / savefig destination
        # ----------------------------------------------------------

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {
                "write_html",
                "savefig",
            }
        ):

            if artifact_dir is None:
                raise UnsafeCodeError(
                    category="artifact_directory",
                    message="Visualization output directory not configured.",
                    suggestion=(
                        "Save charts only after the executor supplies an "
                        "artifact directory."
                    ),
                )

            if not node.args:
                raise UnsafeCodeError(
                    category="artifact_path",
                    message="Visualization output path missing.",
                    suggestion=(
                        "Provide a filename when calling savefig() or "
                        "write_html()."
                    ),
                )

            if (
                not isinstance(node.args[0], ast.Constant)
                or not isinstance(node.args[0].value, str)
            ):
                raise UnsafeCodeError(
                    category="artifact_path",
                    message="Visualization filename must be a string literal.",
                    suggestion=(
                        "Pass a literal filename such as "
                        "'charts/chart_1.png' or 'charts/chart_1.html'."
                    ),
                )

            output_path = (
                os.path.normpath(node.args[0].value)
                .replace("\\", "/")
            )

            if not output_path.startswith(
                normalized_artifact_dir + "/"
            ):
                raise UnsafeCodeError(
                    category="artifact_path",
                    message="Charts must be written inside the artifact directory.",
                    suggestion=(
                        "Save every chart inside the provided artifact directory. "
                        "Do not write files elsewhere."
                    ),
                )

    return tree
# ---------------------------------------------------------------------
# Safe builtins
# ---------------------------------------------------------------------

SAFE_BUILTINS = {
    # Basic types
    "bool": bool,
    "int": int,
    "float": float,
    "str": str,
    "list": list,
    "tuple": tuple,
    "dict": dict,
    "set": set,

    # Iteration
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "reversed": reversed,
    "sorted": sorted,

    # Math
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "pow": pow,

    # Utilities
    "print": print,
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "type": type,

    # Constructors
    "slice": slice,

    # Exceptions
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "KeyError": KeyError,
    "IndexError": IndexError,

    # Import support
    "__import__": __import__,
}

# ---------------------------------------------------------------------
# Visualization path normalizer
# ---------------------------------------------------------------------


def normalize_visualization_artifacts(
    code: str,
    artifact_dir: str,
) -> str:
    """
    Rewrite visualization outputs so every generated chart
    is saved inside the current artifact directory.

    Supported methods

    - fig.write_html(...)
    - fig.write_image(...)
    - fig.write_json(...)
    - plt.savefig(...)
    - fig.savefig(...)
    """

    tree = ast.parse(code, mode="exec")

    artifact_dir = os.path.normpath(
        artifact_dir
    ).replace("\\", "/")

    class ArtifactRewriter(ast.NodeTransformer):

        def __init__(self):
            self.counter = 0

        def visit_Call(self, node):

            self.generic_visit(node)

            if not isinstance(node.func, ast.Attribute):
                return node

            method = node.func.attr

            if method not in {
                "write_html",
                "write_image",
                "write_json",
                "savefig",
            }:
                return node

            self.counter += 1

            if method == "write_html":
                extension = "html"

            elif method == "write_json":
                extension = "json"

            else:
                extension = "png"

            filename = (
                f"{artifact_dir}/chart_{self.counter}.{extension}"
            )

            literal = ast.Constant(value=filename)

            if node.args:
                node.args[0] = literal
            else:
                node.args.append(literal)

            return node

    tree = ArtifactRewriter().visit(tree)

    ast.fix_missing_locations(tree)

    return ast.unparse(tree)