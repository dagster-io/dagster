import functools
import glob

import yaml
from dagster import check

from .merger import deep_merge_dicts


def load_yaml_from_globs(*globs):
    return load_yaml_from_glob_list(list(globs))


def load_yaml_from_glob_list(glob_list):
    check.list_param(glob_list, "glob_list", of_type=str)

    all_files_list = []

    for env_file_pattern in glob_list:
        all_files_list.extend(glob.glob(env_file_pattern))

    return merge_yamls(all_files_list)


def merge_yamls(file_list):
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
        yaml_dict = load_yaml_from_path(yaml_file) or {}

        check.invariant(
            isinstance(yaml_dict, dict),
            (
                "Expected YAML from file {yaml_file} to parse to dictionary, "
                'instead got: "{yaml_dict}"'
            ).format(yaml_file=yaml_file, yaml_dict=yaml_dict),
        )
        merged = deep_merge_dicts(merged, yaml_dict)

    return merged


def merge_yaml_strings(yaml_strs):
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
    yaml_dicts = list([yaml.safe_load(y) for y in yaml_strs])

    for yaml_dict in yaml_dicts:
        check.invariant(
            isinstance(yaml_dict, dict),
            'Expected YAML dictionary, instead got: "%s"' % str(yaml_dict),
        )

    return functools.reduce(deep_merge_dicts, yaml_dicts, {})


def load_yaml_from_path(path):
    check.str_param(path, "path")
    with open(path, "r") as ff:
        return yaml.safe_load(ff)
