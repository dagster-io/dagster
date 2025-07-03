import dagster as dg
import pytest
from dagster._check import ParameterCheckError


def test_asset_resource_double_specify() -> None:
    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements "
        "in both @asset decorator and as arguments to the decorated function",
    ):

        @dg.asset(required_resource_keys={"as_raw_key"})
        def my_asset(context, as_arg: dg.ResourceParam[str]) -> None: ...


def test_multi_asset_resource_double_specify() -> None:
    with pytest.raises(
        ParameterCheckError,
        match="Invariant violation for parameter Cannot specify resource requirements "
        "in both @multi_asset decorator and as arguments to the decorated function",
    ):

        @dg.multi_asset(required_resource_keys={"as_raw_key"})
        def my_multi_asset(context, as_arg: dg.ResourceParam[str]) -> None: ...
