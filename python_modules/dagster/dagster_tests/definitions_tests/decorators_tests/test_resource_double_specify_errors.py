import pytest
from dagster import ResourceParam, asset, multi_asset
from dagster._check import ParameterCheckError


def test_asset_resource_double_specify() -> None:
    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements "
        "in both @asset decorator and as arguments to the decorated function",
    ):

        @asset(required_resource_keys={"as_raw_key"})
        def my_asset(context, as_arg: ResourceParam[str]) -> None: ...


def test_multi_asset_resource_double_specify() -> None:
    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements "
        "in both @multi_asset decorator and as arguments to the decorated function",
    ):

        @multi_asset(required_resource_keys={"as_raw_key"})
        def my_multi_asset(context, as_arg: ResourceParam[str]) -> None: ...
