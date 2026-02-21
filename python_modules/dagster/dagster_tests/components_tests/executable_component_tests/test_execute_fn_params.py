import dagster as dg
import pytest
from dagster.components.lib.executable_component.function_component import ExecuteFnMetadata
from dagster_shared.check import CheckError


def test_execute_fn_with_ok() -> None:
    def execute_fn_no_args(context): ...

    invoker = ExecuteFnMetadata(execute_fn_no_args)
    assert invoker.resource_keys == set()
    assert invoker.function_params_names == {"context"}


def test_execute_fn_no_annotations() -> None:
    def execute_fn(context, no_annotation): ...

    with pytest.raises(CheckError, match=r"Found extra arguments in execute_fn: {'no_annotation'}"):
        ExecuteFnMetadata(execute_fn)


def test_execute_fn_with_resource_param() -> None:
    def execute_fn(context, some_resource: dg.ResourceParam[str]): ...

    invoker = ExecuteFnMetadata(execute_fn)
    assert invoker.resource_keys == {"some_resource"}
    assert invoker.function_params_names == {"context", "some_resource"}
