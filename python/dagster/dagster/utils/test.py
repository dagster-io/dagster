import inspect
import itertools
import os
import tempfile
from contextlib import contextmanager

from dagster import check


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


def _unlink_swallow_errors(path):
    check.str_param(path, 'path')
    try:
        os.unlink(path)
    except:  # pylint: disable=W0702
        pass


@contextmanager
def get_temp_file_name():
    temp_file_name = tempfile.mkstemp()[1]
    try:
        yield temp_file_name
    finally:
        _unlink_swallow_errors(temp_file_name)


@contextmanager
def get_temp_file_names(number):
    check.int_param(number, 'number')

    temp_file_names = list()
    for _ in itertools.repeat(None, number):
        temp_file_name = tempfile.mkstemp()[1]
        temp_file_names.append(temp_file_name)

    try:
        yield tuple(temp_file_names)
    finally:
        for temp_file_name in temp_file_names:
            _unlink_swallow_errors(temp_file_name)
