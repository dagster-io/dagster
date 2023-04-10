import datetime

from dagster import (
    AssetIn,
    Definitions,
    asset,
    input_manager,
    observable_source_asset,
)
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import Output
from dagster._core.definitions.source_asset import SourceAsset


@observable_source_asset(
    key_prefix=["data_versions"],
)
def foo(_context):
    return DataVersion(str(datetime.datetime.now()))


@observable_source_asset(
    key_prefix=["data_versions"],
)
def bar(_context):
    return DataVersion(str(datetime.datetime.now()))


baz = SourceAsset("baz")


@input_manager
def source_asset_input_manager():
    return 100


@asset(
    key_prefix=["data_versions"],
    ins={"foo": AssetIn(input_manager_key="source_asset_input_manager")},
    code_version="1",
)
def alpha(context, foo):
    return foo + 100


@asset(
    key_prefix=["data_versions"],
    ins={"bar": AssetIn(input_manager_key="source_asset_input_manager")},
    code_version="1",
)
def beta(context, bar):
    return bar + 100


@asset(
    key_prefix=["data_versions"],
    ins={
        "foo": AssetIn(input_manager_key="source_asset_input_manager"),
        "bar": AssetIn(input_manager_key="source_asset_input_manager"),
        "baz": AssetIn(input_manager_key="source_asset_input_manager"),
    },
    code_version="1",
)
def delta(context, foo, bar, baz):
    return foo + bar + baz + 100


@asset(
    key_prefix=["data_versions"],
    code_version="1",
)
def epsilon(context, alpha):
    return alpha + 100


@asset(
    key_prefix=["data_versions"],
)
def gamma(context):
    return 100


@asset(
    key_prefix=["data_versions"],
)
def rho(context, gamma):
    return gamma + 100


@multi_asset(
    outs={
        "sigma": AssetOut(key_prefix="data_versions", code_version="1"),
        "tau": AssetOut(key_prefix="data_versions", code_version="3"),
    },
)
def sigma_tau(context, rho):
    yield Output(rho + 100, "sigma")
    yield Output(rho + 200, "tau")


@asset(key_prefix=["data_versions"], ins={"tau": AssetIn("tau")})
def zeta(context, tau):
    return tau + 100


definitions = Definitions(
    assets=[foo, bar, baz, alpha, beta, delta, epsilon, gamma, rho, sigma_tau, zeta],
    resources={"source_asset_input_manager": source_asset_input_manager},
)
