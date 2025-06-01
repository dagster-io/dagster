from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Optional, TypeVar, overload

from dagster._core.events import DagsterEvent
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext

T = TypeVar("T")


@overload
@contextmanager
def load_input(context: AssetExecutionContext, input_name: str) -> Iterator[Any]: ...


@overload
@contextmanager
def load_input(
    context: AssetExecutionContext, input_name: str, expected_type: type[T]
) -> Iterator[T]: ...


@contextmanager
def load_input(
    context: AssetExecutionContext, input_name: str, expected_type: Optional[type[T]] = None
) -> Iterator[Any]:
    step_context = context.get_step_execution_context()
    step_input = step_context.step.step_input_named(input_name)
    input_def = step_context.op_def.input_def_named(input_name)
    iterator = step_input.source.load_input_object(step_context, input_def)
    for item in iterator:
        if isinstance(item, DagsterEvent):
            context.op_execution_context._events.append(item)  # noqa: SLF001
        else:
            if expected_type is not None:
                assert isinstance(item, expected_type)
            yield item
