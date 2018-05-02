from contextlib import contextmanager
import inspect
import os
import tempfile

import check


def script_relative_path(file_path):
    '''
    Useful for testing repos. Place a repo directory within your tests
    directly and you can load a handle to query and manipulate it. This
    will be relative to the *caller* of script_relative_handle.
    '''
    # from http://bit.ly/2snyC6s

    check.str_param(file_path, 'file_path')
    scriptdir = inspect.stack()[1][1]
    return os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path)


@contextmanager
def get_temp_file_name():
    temp_file_name = tempfile.mkstemp()[1]
    try:
        yield temp_file_name
    finally:
        os.unlink(temp_file_name)
