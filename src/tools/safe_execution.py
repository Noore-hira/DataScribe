"""Small guardrail for model-produced analysis code.

This is not a security boundary for hostile code. It blocks common unsafe
operations and removes powerful Python builtins; production deployments should
run generated code in a separate sandboxed worker.
"""

import ast


class UnsafeCodeError(ValueError):
    pass


_BANNED_NAMES = {"open", "exec", "eval", "compile", "input", "__import__", "globals", "locals", "vars", "getattr", "setattr", "delattr"}
_BANNED_ATTRIBUTES = {"read_csv", "read_excel", "read_parquet", "read_json", "to_csv", "to_excel", "to_pickle", "to_sql", "write_html", "savefig", "save", "system", "popen", "remove", "unlink", "rmtree"}
_BANNED_NODES = (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.Global, ast.Nonlocal)


def validate_analysis_code(code: str, *, artifact_dir: str | None = None) -> ast.Module:
    tree = ast.parse(code, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, _BANNED_NODES):
            raise UnsafeCodeError(f"Unsupported statement: {type(node).__name__}")
        if isinstance(node, ast.Name) and (node.id in _BANNED_NAMES or node.id.startswith("__")):
            raise UnsafeCodeError(f"Unsafe name: {node.id}")
        allowed_artifact_method = isinstance(node, ast.Attribute) and artifact_dir and node.attr in {"write_html", "savefig"}
        if isinstance(node, ast.Attribute) and (not allowed_artifact_method and (node.attr in _BANNED_ATTRIBUTES or node.attr.startswith("__"))):
            raise UnsafeCodeError(f"Unsafe attribute: {node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"write_html", "savefig"}:
            if not artifact_dir or not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                raise UnsafeCodeError("Chart files must use a literal path in the run artifact directory")
            if not node.args[0].value.replace("\\", "/").startswith(f"{artifact_dir}/"):
                raise UnsafeCodeError("Chart files must be saved in the run artifact directory")
    return tree


SAFE_BUILTINS = {
    "print": print,
    "len": len,
    "round": round,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "sum": sum,
    "min": min,
    "max": max,
    "range": range,
}


def normalize_visualization_artifacts(code: str, artifact_dir: str) -> str:
    """Force every chart-save call into the current run's artifact directory."""

    tree = ast.parse(code, mode="exec")

    class ArtifactRewriter(ast.NodeTransformer):
        def __init__(self) -> None:
            self.counter = 0

        def visit_Call(self, node: ast.Call):
            self.generic_visit(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"write_html", "savefig"}:
                self.counter += 1
                suffix = "html" if node.func.attr == "write_html" else "png"
                path = f"{artifact_dir}/chart_{self.counter}.{suffix}"
                if node.args:
                    node.args[0] = ast.Constant(path)
                else:
                    node.args.append(ast.Constant(path))
            return node

    rewritten = ArtifactRewriter().visit(tree)
    ast.fix_missing_locations(rewritten)
    return ast.unparse(rewritten)
