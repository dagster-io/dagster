import functools
import glob
from typing import Any, Dict

import yaml

import dagster._check as check

from .merger import deep_merge_dicts

YAML_TIMESTAMP_TAG = "tag:yaml.org,2002:timestamp"
YAML_STR_TAG = "tag:yaml.org,2002:str"


class _CanRemoveImplicitResolver:
    # Adds a "remove_implicit_resolver" method that can be used to selectively
    # disable default PyYAML resolvers
    @classmethod
    def remove_implicit_resolver(cls, tag):
        # See https://github.com/yaml/pyyaml/blob/master/lib/yaml/resolver.py#L26 for inspiration
        if not "yaml_implicit_resolvers" in cls.__dict__:
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


def load_yaml_from_globs(*globs, loader=DagsterRunConfigYamlLoader):
    return load_yaml_from_glob_list(list(globs), loader=loader)


def load_yaml_from_glob_list(glob_list, loader=DagsterRunConfigYamlLoader):
    check.list_param(glob_list, "glob_list", of_type=str)

    all_files_list = []

    for env_file_pattern in glob_list:
        all_files_list.extend(glob.glob(env_file_pattern))

    return merge_yamls(all_files_list, loader=loader)


def merge_yamls(file_list, loader=DagsterRunConfigYamlLoader):
    """Combine a list of YAML files into a dictionary.

    Args:
        file_list (List[str]): List of YAML filenames

    Returns:
        dict: Merged dictionary from combined YAMLs

    Raises:
        yaml.YAMLError: When one of the YAML documents is invalid and has a parse error.
    """
    check.list_param(file_list, "file_list", of_type=str)

    merged = {}

    for yaml_file in file_list:
        yaml_dict = load_yaml_from_path(yaml_file, loader=loader) or {}

        check.invariant(
            isinstance(yaml_dict, dict),
            (
                "Expected YAML from file {yaml_file} to parse to dictionary, "
                'instead got: "{yaml_dict}"'
            ).format(yaml_file=yaml_file, yaml_dict=yaml_dict),
        )
        merged = deep_merge_dicts(merged, yaml_dict)

    return merged


def merge_yaml_strings(yaml_strs, loader=DagsterRunConfigYamlLoader):
    """Combine a list of YAML strings into a dictionary.  Right-most overrides left-most.

    Args:
        yaml_strs (List[str]): List of YAML strings

    Returns:
        dict: Merged dictionary from combined YAMLs

    Raises:
        yaml.YAMLError: When one of the YAML documents is invalid and has a parse error.
    """
    check.list_param(yaml_strs, "yaml_strs", of_type=str)

    # Read YAML strings.
    yaml_dicts = list([yaml.load(y, Loader=loader) for y in yaml_strs])

    for yaml_dict in yaml_dicts:
        check.invariant(
            isinstance(yaml_dict, dict),
            'Expected YAML dictionary, instead got: "%s"' % str(yaml_dict),
        )

    return functools.reduce(deep_merge_dicts, yaml_dicts, {})


def load_yaml_from_path(path: str, loader=DagsterRunConfigYamlLoader) -> object:
    check.str_param(path, "path")
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=loader)


def load_run_config_yaml(yaml_str: str):
    return yaml.load(yaml_str, Loader=DagsterRunConfigYamlLoader)


def dump_run_config_yaml(run_config: Dict[str, Any]) -> str:
    return yaml.dump(
        run_config, Dumper=DagsterRunConfigYamlDumper, default_flow_style=False, allow_unicode=True
    )
