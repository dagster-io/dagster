import inspect
import os
import re
import yaml

from dagster import check

from .yaml_utils import (
    load_yaml_from_path,
    load_yaml_from_glob_list,
)


def script_relative_path(file_path):
    '''
    Useful for testing with local files. Use a path relative to where the
    test resides and this function will return the absolute path
    of that file. Otherwise it will be relative to script that
    ran the test
    '''
    # from http://bit.ly/2snyC6s

    check.str_param(file_path, 'file_path')
    scriptdir = inspect.stack()[1][1]
    return os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path)


# Adapted from https://github.com/okunishinishi/python-stringcase/blob/master/stringcase.py
def camelcase(string):
    check.str_param(string, 'string')

    string = re.sub(r'^[\-_\.]', '', str(string))
    if not string:
        return string
    return str(string[0]).upper() + re.sub(
        r'[\-_\.\s]([a-z])',
        lambda matched: str(matched.group(1)).upper(),
        string[1:],
    )
