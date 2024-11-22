from types import TracebackType
from typing import Tuple, Type, Union

ExcInfo = Union[tuple[type[BaseException], BaseException, TracebackType], tuple[None, None, None]]
