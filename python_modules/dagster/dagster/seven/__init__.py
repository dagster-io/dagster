from .json import dump, dumps, JSONDecodeError
from .temp_dir import get_system_temp_directory

try:
    FileNotFoundError = FileNotFoundError  # pylint:disable=redefined-builtin
except NameError:
    FileNotFoundError = IOError
