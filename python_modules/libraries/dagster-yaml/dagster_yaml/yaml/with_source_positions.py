from dataclasses import dataclass
from typing import Any, cast

import yaml

from .source_position import KeyPathSegment, LineCol, SourcePosition, SourcePositionTreeNode


@dataclass(frozen=True)
class ValueAndTreeNode:
    value: Any
    tree_node: SourcePositionTreeNode


def parse_yaml_with_source_positions(
    src: str,
    filename: str = "<string>",
    implicits_to_remove: list[str] = ["tag:yaml.org,2002:timestamp"],
) -> ValueAndTreeNode:
    """Parse YAML source with source position information.

    This function takes a YAML source string and an optional filename, and returns a
    `ValueAndTreeNode` object. The `ValueAndTreeNode` contains the parsed YAML value and a
    `SourcePositionTreeNode` that holds the source position information for the YAML structure.

    The function uses a custom YAML loader (`SafeLineLoader`) that tracks the source position
    information for each YAML node. It also allows for the removal of specific implicit resolvers,
    such as the default timestamp resolver.

    Args:
        src (str): The YAML source string to be parsed.
        filename (str): The filename associated with the YAML source, used for error reporting.
            Defaults to "<string>" if not provided.
        implicits_to_remove (list[str]): A list of YAML implicit resolvers to remove. Defaults to
            removing the timestamp resolver.

    Returns:
        ValueAndTreeNode: An object containing the parsed YAML value and the corresponding source
            position information.
    """

    class SafeLineLoader(yaml.SafeLoader):
        @classmethod
        def remove_implicit_resolver(cls, tag_to_remove: Any):
            if "yaml_implicit_resolvers" not in cls.__dict__:
                cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

            for first_letter, mappings in cls.yaml_implicit_resolvers.items():
                cls.yaml_implicit_resolvers[first_letter] = [
                    (tag, regexp) for tag, regexp in mappings if tag != tag_to_remove
                ]

        def construct_object(self, node: Any, deep: Any = False):
            value = super().construct_object(node, True)
            source_position = SourcePosition(
                filename=filename,
                start=LineCol(
                    line=node.start_mark.line + 1,
                    col=node.start_mark.column + 1,
                ),
                end=LineCol(
                    line=node.end_mark.line + 1,
                    col=node.end_mark.column + 1,
                ),
            )

            if isinstance(value, dict):
                dict_rv: dict[Any, Any] = {}
                child_trie_nodes: dict[KeyPathSegment, SourcePositionTreeNode] = {}
                for k, v in cast(dict[ValueAndTreeNode, ValueAndTreeNode], value).items():
                    dict_rv[k.value] = v.value
                    child_trie_nodes[k.value] = v.tree_node
                return ValueAndTreeNode(
                    dict_rv,
                    SourcePositionTreeNode(position=source_position, children=child_trie_nodes),
                )
            if isinstance(value, list):
                list_rv: list[Any] = []
                child_trie_nodes: dict[KeyPathSegment, SourcePositionTreeNode] = {}
                for i, v in enumerate(cast(list[ValueAndTreeNode], value)):
                    list_rv.append(v.value)
                    child_trie_nodes[i] = v.tree_node
                return ValueAndTreeNode(
                    list_rv,
                    SourcePositionTreeNode(position=source_position, children=child_trie_nodes),
                )

            return ValueAndTreeNode(
                value,
                SourcePositionTreeNode(position=source_position, children={}),
            )

    for implicit_to_remove in implicits_to_remove:
        SafeLineLoader.remove_implicit_resolver(implicit_to_remove)

    try:
        value_and_tree_node = yaml.load(src, Loader=SafeLineLoader)
    except yaml.MarkedYAMLError as e:
        if e.context_mark is not None:
            e.context_mark.name = filename
        if e.problem_mark is not None:
            e.problem_mark.name = filename
        raise e

    return value_and_tree_node
