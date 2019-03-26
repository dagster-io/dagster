'''Internal py2/3 compatibility library. A little more than six.'''

import sys

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
