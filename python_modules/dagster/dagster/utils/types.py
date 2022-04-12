from types import TracebackType
from typing import Tuple, Type, Union

ExcInfo = Union[Tuple[Type[BaseException], BaseException, TracebackType], Tuple[None, None, None]]
