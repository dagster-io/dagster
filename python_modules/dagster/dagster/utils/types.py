from types import TracebackType   # pylint: disable=no-name-in-module; (false positive)
from typing import Tuple, Type, Union

ExcInfo = Union[Tuple[Type[BaseException], BaseException, TracebackType], Tuple[None, None, None]]
