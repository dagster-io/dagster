"""ariadne-codegen plugins applied when regenerating ``__generated__``."""

import ast

from ariadne_codegen.plugins.base import Plugin  # ty: ignore[unresolved-import]
from graphql import FragmentDefinitionNode

# builtin generics whose args python 3.10 refuses to resolve, and their typing equivalents
_TYPING_EQUIVALENT = {"list": "List", "dict": "Dict", "set": "Set", "tuple": "Tuple"}


class TypingGenericsInFragmentsPlugin(Plugin):
    """Rewrite ``list["Foo"]`` to ``List["Foo"]`` in the fragments module.

    Query modules subclass fragment classes, inheriting annotations that name types defined
    only in ``fragments.py``. Python 3.10's ``typing._eval_type`` leaves a bare string arg of
    a builtin generic untouched, so the forward ref survives into the subclass and pydantic
    raises ``PydanticUndefinedAnnotation`` when it rebuilds the model against the query
    module's namespace. ``typing.List`` resolves on every supported version.

    A union arg (``list[Union["A", "B"]]``) is already a ``ForwardRef`` by then and resolves
    fine, so only the single-type case is rewritten. Delete this once 3.10 support ends.
    """

    def generate_fragments_module(
        self,
        module: ast.Module,
        fragments_definitions: dict[str, FragmentDefinitionNode],
    ) -> ast.Module:
        module = _TypingGenericRewriter().visit(module)
        # isort merges this into the existing typing import; autoflake drops what went unused
        module.body.insert(
            0,
            ast.ImportFrom(
                module="typing",
                names=[ast.alias(name=name) for name in _TYPING_EQUIVALENT.values()],
                level=0,
            ),
        )
        return ast.fix_missing_locations(module)


class _TypingGenericRewriter(ast.NodeTransformer):
    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        self.generic_visit(node)
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in _TYPING_EQUIVALENT
            and _is_forward_ref(node.slice)
        ):
            node.value = ast.Name(id=_TYPING_EQUIVALENT[node.value.id], ctx=ast.Load())
        return node


def _is_forward_ref(node: ast.expr) -> bool:
    """ariadne-codegen emits forward refs as a Name carrying its own quotes."""
    return isinstance(node, ast.Name) and node.id.startswith(('"', "'"))
