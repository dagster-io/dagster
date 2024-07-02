from types import TracebackType
from typing import Type, Tuple, Union

ExcInfo = Union[Tuple[Type[BaseException], BaseException, TracebackType], Tuple[None, None, None]]
