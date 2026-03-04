from types import TracebackType
from typing import TypeAlias

ExcInfo: TypeAlias = (
    tuple[type[BaseException], BaseException, TracebackType] | tuple[None, None, None]
)
