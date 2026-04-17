from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class DagsterInstanceContext(ABC):
    @property
    @abstractmethod
    def instance(self) -> "DagsterInstance": ...

    @abstractmethod
    def create_instance(self) -> Optional["DagsterInstance"]: ...


_current_ctx: ContextVar[Optional[DagsterInstanceContext]] = ContextVar(
    "current_dagster_instance_context", default=None
)


@contextmanager
def set_dagster_instance_context(
    new_ctx: DagsterInstanceContext,
) -> Iterator[DagsterInstanceContext]:
    token = _current_ctx.set(new_ctx)

    try:
        yield new_ctx
    finally:
        _current_ctx.reset(token)


def get_dagster_instance_context() -> Optional[DagsterInstanceContext]:
    return _current_ctx.get()
