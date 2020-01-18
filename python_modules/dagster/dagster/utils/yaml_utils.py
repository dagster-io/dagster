import glob

import yaml

from dagster import check

from .merger import dict_merge


def load_yaml_from_globs(*globs):
    return load_yaml_from_glob_list(list(globs))


def load_yaml_from_glob_list(glob_list):
    check.list_param(glob_list, 'glob_list', of_type=str)

    all_files_list = []

    for env_file_pattern in glob_list:
        all_files_list.extend(glob.glob(env_file_pattern))

    return merge_yamls(all_files_list)


def merge_yamls(file_list):
    check.list_param(file_list, 'file_list', of_type=str)
    merged = {}
    for yaml_file in file_list:
        merged = dict_merge(load_yaml_from_path(yaml_file) or {}, merged)
    return merged


def load_yaml_from_path(path):
    check.str_param(path, 'path')
    with open(path, 'r') as ff:
        return yaml.safe_load(ff)
