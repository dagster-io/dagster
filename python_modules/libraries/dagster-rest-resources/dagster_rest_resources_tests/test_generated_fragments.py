"""Guards on the shape of the generated fragments module."""

import ast
from pathlib import Path

import dagster_rest_resources

FRAGMENTS = Path(dagster_rest_resources.__file__).parent / "__generated__" / "fragments.py"

_BUILTIN_GENERICS = {"list", "dict", "set", "tuple"}


def _forward_refs_under_builtin_generics(tree: ast.AST) -> list[str]:
    return [
        f"{node.value.id}[{node.slice.value!r}] on line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id in _BUILTIN_GENERICS
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
    ]


def test_no_forward_refs_under_builtin_generics():
    """Query modules subclass these fragments, so their annotations must survive the move.

    Python 3.10 does not resolve a bare forward ref inside ``list[...]``, which leaves the
    subclass unbuildable. ``TypingGenericsInFragmentsPlugin`` rewrites them to ``typing.List``
    at generation time; this fails if the plugin is dropped from the codegen config.
    """
    offenders = _forward_refs_under_builtin_generics(ast.parse(FRAGMENTS.read_text()))
    assert not offenders, (
        "regenerate with TypingGenericsInFragmentsPlugin enabled; unresolvable on py3.10: "
        + ", ".join(offenders)
    )
