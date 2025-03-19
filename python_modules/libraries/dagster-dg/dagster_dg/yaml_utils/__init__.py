## Lifted from dagster._utils.yaml_utils
from collections.abc import Mapping, Sequence
from typing import Any, cast

import yaml

from dagster_dg.yaml_utils.source_position import (
    KeyPathSegment,
    LineCol,
    SourcePosition,
    SourcePositionTree,
    ValueAndSourcePositionTree,
)

# Removing this implicit loader stops YAML-loading from returning datetime objects
YAML_TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"


class _CanRemoveImplicitResolver:
    # Adds a "remove_implicit_resolver" method that can be used to selectively
    # disable default PyYAML resolvers

    @classmethod
    def remove_implicit_resolver(cls, tag):
        # See https://github.com/yaml/pyyaml/blob/master/lib/yaml/resolver.py#L26 for inspiration
        if "yaml_implicit_resolvers" not in cls.__dict__:
            implicit_resolvers = {}
            for key in cls.yaml_implicit_resolvers:
                implicit_resolvers[key] = cls.yaml_implicit_resolvers[key][:]
            cls.yaml_implicit_resolvers = implicit_resolvers

        for ch, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[ch] = [
                (existing_tag, regexp) for existing_tag, regexp in mappings if existing_tag != tag
            ]


def parse_yaml_with_source_positions(
    src: str,
    filename: str = "<string>",
    implicits_to_remove: Sequence[str] = [YAML_TIMESTAMP_TAG],
) -> ValueAndSourcePositionTree:
    """Parse YAML source with source position information.
    This function takes a YAML source string and an optional filename, and returns a
    `ValueAndSourcePositionTree` object. The `ValueAndSourcePositionTree` contains the
    parsed YAML value and a `SourcePositionTree` that holds the source position information for
    the YAML structure.

    The function uses a custom YAML loader (`SourcePositionLoader`) that tracks the source position
    information for each YAML node. It also allows for the removal of specific implicit resolvers,
    such as the default timestamp resolver.

    Args:
        src (str): The YAML source string to be parsed.
        filename (str): The filename associated with the YAML source, used for error reporting.
            Defaults to "<string>" if not provided.
        implicits_to_remove (list[str]): A list of YAML implicit resolvers to remove. Defaults to
            removing the timestamp resolver.

    Returns:
        ValueAndSourcePositionTree: An object containing the parsed YAML value and the corresponding
            source position information.
    """

    class SourcePositionLoader(yaml.SafeLoader, _CanRemoveImplicitResolver):
        def construct_object(self, node: Any, deep: Any = False) -> ValueAndSourcePositionTree:
            """Returns a ValueAndSourcePositionTree object where:
            - Its value is what the regular yaml.SafeLoader returns
            - Its source_position_tree is a tree where each node corresponds to a node in the YAML
              tree.
            """
            source_position = SourcePosition(
                filename=filename,
                start=LineCol(line=node.start_mark.line + 1, col=node.start_mark.column + 1),
                end=LineCol(line=node.end_mark.line + 1, col=node.end_mark.column + 1),
            )

            value = super().construct_object(node, True)
            # If value is a collection, then all of its elements will be ValueAndSourcePositionTree
            # instances. We need to do two things:
            # - Strip out the enclosing ValueAndSourcePositionTrees, so we're just returning a
            #   collection of the raw values
            # - Assemble the source position subtrees into a super-tree

            if isinstance(value, dict):
                dict_with_raw_values: dict[Any, Any] = {}
                child_trees: dict[KeyPathSegment, SourcePositionTree] = {}
                for k, v in cast(
                    Mapping[ValueAndSourcePositionTree, ValueAndSourcePositionTree], value
                ).items():
                    dict_with_raw_values[k.value] = v.value
                    child_trees[k.value] = SourcePositionTree(
                        position=k.source_position_tree.position,
                        children=v.source_position_tree.children,
                    )
                return ValueAndSourcePositionTree(
                    dict_with_raw_values,
                    SourcePositionTree(position=source_position, children=child_trees),
                )
            if isinstance(value, list):
                list_with_raw_values: list[Any] = []
                child_trees: dict[KeyPathSegment, SourcePositionTree] = {}
                for i, v in enumerate(cast(Sequence[ValueAndSourcePositionTree], value)):
                    list_with_raw_values.append(v.value)
                    child_trees[i] = v.source_position_tree
                return ValueAndSourcePositionTree(
                    list_with_raw_values,
                    SourcePositionTree(position=source_position, children=child_trees),
                )

            return ValueAndSourcePositionTree(
                value,
                SourcePositionTree(position=source_position, children={}),
            )

    for implicit_to_remove in implicits_to_remove:
        SourcePositionLoader.remove_implicit_resolver(implicit_to_remove)

    try:
        value_and_tree_node = yaml.load(src, Loader=SourcePositionLoader)
    except yaml.MarkedYAMLError as e:
        if e.context_mark is not None:
            e.context_mark.name = filename
        if e.problem_mark is not None:
            e.problem_mark.name = filename
        raise e

    return value_and_tree_node
