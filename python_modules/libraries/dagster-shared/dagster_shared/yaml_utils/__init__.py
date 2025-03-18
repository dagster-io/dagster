import functools
import glob
from collections.abc import Mapping, Sequence
from typing import Any, cast

import yaml

import dagster_shared.check as check
from dagster_shared.merger import deep_merge_dicts
from dagster_shared.yaml_utils.source_position import (
    KeyPathSegment,
    LineCol,
    SourcePosition,
    SourcePositionTree,
    ValueAndSourcePositionTree,
)

# Removing this implicit loader stops YAML-loading from returning datetime objects
YAML_TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"
YAML_STR_TAG = "tag:yaml.org,2002:str"


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


# Handles strings with leading 0s being unexpectedly parsed as octal ints
# See: https://github.com/yaml/pyyaml/issues/98#issuecomment-436814271
def _octal_string_representer(dumper, value):
    if value.startswith("0"):
        return dumper.represent_scalar(YAML_STR_TAG, value, style="'")
    return dumper.represent_scalar(YAML_STR_TAG, value)


class DagsterRunConfigYamlLoader(yaml.SafeLoader, _CanRemoveImplicitResolver):
    pass


DagsterRunConfigYamlLoader.remove_implicit_resolver(YAML_TIMESTAMP_TAG)


class DagsterRunConfigYamlDumper(yaml.SafeDumper, _CanRemoveImplicitResolver):
    pass


DagsterRunConfigYamlDumper.remove_implicit_resolver(YAML_TIMESTAMP_TAG)
DagsterRunConfigYamlDumper.add_representer(str, _octal_string_representer)


def load_yaml_from_globs(
    *globs: str, loader: type[yaml.SafeLoader] = DagsterRunConfigYamlLoader
) -> Mapping[object, object]:
    return load_yaml_from_glob_list(list(globs), loader=loader)


def load_yaml_from_glob_list(
    glob_list: Sequence[str], loader: type[yaml.SafeLoader] = DagsterRunConfigYamlLoader
) -> Mapping[object, object]:
    check.sequence_param(glob_list, "glob_list", of_type=str)

    all_files_list: list[str] = []

    for env_file_pattern in glob_list:
        all_files_list.extend(glob.glob(env_file_pattern))

    return merge_yamls(all_files_list, loader=loader)


def merge_yamls(
    file_list: Sequence[str], loader: type[yaml.SafeLoader] = DagsterRunConfigYamlLoader
) -> dict[object, object]:
    """Combine a list of YAML files into a dictionary.

    Args:
        file_list (List[str]): List of YAML filenames

    Returns:
        dict: Merged dictionary from combined YAMLs

    Raises:
        yaml.YAMLError: When one of the YAML documents is invalid and has a parse error.
    """
    check.sequence_param(file_list, "file_list", of_type=str)

    merged: dict[object, object] = {}

    for yaml_file in file_list:
        yaml_dict = load_yaml_from_path(yaml_file, loader=loader) or {}

        if isinstance(yaml_dict, dict):
            merged = deep_merge_dicts(merged, yaml_dict)
        else:
            check.failed(
                f"Expected YAML from file {yaml_file} to parse to dictionary, "
                f'instead got: "{yaml_dict}"'
            )
    return merged


def merge_yaml_strings(
    yaml_strs: Sequence[str], loader: type[yaml.SafeLoader] = DagsterRunConfigYamlLoader
) -> dict[object, object]:
    """Combine a list of YAML strings into a dictionary.  Right-most overrides left-most.

    Args:
        yaml_strs (List[str]): List of YAML strings

    Returns:
        dict: Merged dictionary from combined YAMLs

    Raises:
        yaml.YAMLError: When one of the YAML documents is invalid and has a parse error.
    """
    check.sequence_param(yaml_strs, "yaml_strs", of_type=str)

    # Read YAML strings.
    yaml_dicts = list([yaml.load(y, Loader=loader) for y in yaml_strs])

    for yaml_dict in yaml_dicts:
        check.invariant(
            isinstance(yaml_dict, dict),
            f'Expected YAML dictionary, instead got: "{yaml_dict!s}"',
        )

    return functools.reduce(deep_merge_dicts, yaml_dicts, {})


def load_yaml_from_path(
    path: str, loader: type[yaml.SafeLoader] = DagsterRunConfigYamlLoader
) -> object:
    check.str_param(path, "path")
    with open(path, encoding="utf8") as ff:
        return yaml.load(ff, Loader=loader)


def load_run_config_yaml(yaml_str: str) -> Mapping[str, object]:
    return yaml.load(yaml_str, Loader=DagsterRunConfigYamlLoader)


def dump_run_config_yaml(run_config: Mapping[str, Any], sort_keys: bool = True) -> str:
    return yaml.dump(
        run_config,
        Dumper=DagsterRunConfigYamlDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=sort_keys,
    )


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
