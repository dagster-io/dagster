from types import TracebackType
from typing import Union

ExcInfo = Union[tuple[type[BaseException], BaseException, TracebackType], tuple[None, None, None]]
