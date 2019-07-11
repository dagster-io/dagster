'''Internal py2/3 compatibility library. A little more than six.'''

import os
import sys
import time

from .json import dump, dumps, JSONDecodeError
from .temp_dir import get_system_temp_directory

try:
    FileNotFoundError = FileNotFoundError  # pylint:disable=redefined-builtin
except NameError:
    FileNotFoundError = IOError

if sys.version_info.major >= 3:
    from io import StringIO  # pylint:disable=import-error
else:
    from StringIO import StringIO  # pylint:disable=import-error


if sys.version_info.major >= 3:
    from urllib.request import urlretrieve  # pylint:disable=import-error
else:
    from urllib import urlretrieve  # pylint:disable=no-name-in-module


# TODO implement a generic import by name -- see https://stackoverflow.com/questions/301134/how-to-import-a-module-given-its-name

# https://stackoverflow.com/a/67692/324449
def import_module_from_path(module_name, path_to_file):
    version = sys.version_info
    if version.major >= 3 and version.minor >= 5:
        import importlib.util

        spec = importlib.util.spec_from_file_location(module_name, path_to_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    elif version.major >= 3 and version.minor >= 3:
        from importlib.machinery import SourceFileLoader

        # pylint:disable=deprecated-method, no-value-for-parameter
        module = SourceFileLoader(module_name, path_to_file).load_module()
    else:
        from imp import load_source

        module = load_source(module_name, path_to_file)

    return module


# https://stackoverflow.com/a/437591/324449
def reload_module(module):
    version = sys.version_info
    if version.major >= 3 and version.minor >= 4:
        from importlib import reload as reload_

        return reload_(module)
    elif version.major >= 3:
        from imp import reload as reload_

        return reload_(module)

    return reload(module)  # pylint: disable=undefined-variable


def is_ascii(str_):
    if sys.version_info.major < 3:
        try:
            str_.decode('ascii')
            return True
        except UnicodeEncodeError:
            return False
    elif sys.version_info.major == 3 and sys.version_info.minor < 7:
        try:
            str_.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False
    else:
        return str_.isascii()


if sys.version_info.major >= 3 and sys.version_info.minor >= 3:
    time_fn = time.perf_counter
elif os.name == 'nt':
    time_fn = time.clock
else:
    time_fn = time.time

try:
    from unittest import mock
except ImportError:
    # Because this dependency is not encoded setup.py deliberately
    # (we do not want to override or conflict with our users mocks)
    # we never fail when importing this.

    # This will only be used within *our* test enviroment of which
    # we have total control
    try:
        import mock
    except ImportError:
        pass
