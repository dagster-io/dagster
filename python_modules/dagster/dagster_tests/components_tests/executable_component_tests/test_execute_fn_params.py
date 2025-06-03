from typing import Annotated

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.resource_annotation import ResourceParam
from dagster.components.lib.executable_component.component import (
    ExecuteFnMetadata,
    Upstream,
    get_upstream_args,
)
from dagster_shared.check import CheckError


def test_execute_fn_with_ok() -> None:
    def execute_fn_no_args(context): ...

    invoker = ExecuteFnMetadata(execute_fn_no_args)
    assert invoker.resource_keys == set()
    assert invoker.function_params_names == {"context"}


def test_execute_fn_no_annotations() -> None:
    def execute_fn(context, no_annotation): ...

    with pytest.raises(CheckError, match="Found extra arguments in execute_fn: {'no_annotation'}"):
        ExecuteFnMetadata(execute_fn)


def test_execute_fn_with_resource_param() -> None:
    def execute_fn(context, some_resource: ResourceParam[str]): ...

    invoker = ExecuteFnMetadata(execute_fn)
    assert invoker.resource_keys == {"some_resource"}
    assert invoker.function_params_names == {"context", "some_resource"}


def test_execute_fn_with_explicit_asset_key() -> None:
    def execute_fn(context, some_upstream: Annotated[str, Upstream(asset_key="some_upstream")]): ...

    invoker = ExecuteFnMetadata(execute_fn)
    assert AssetKey("some_upstream") in invoker.upstreams_by_asset_key


def test_upstream_args() -> None:
    def execute_fn(context, some_upstream: Annotated[str, Upstream(asset_key="some_upstream")]): ...

    args = get_upstream_args(execute_fn)
    assert set(args.keys()) == {"some_upstream"}
    assert args["some_upstream"].type is str
    assert isinstance(args["some_upstream"].asset_key, AssetKey)
    assert args["some_upstream"].asset_key.to_user_string() == "some_upstream"
