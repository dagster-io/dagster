import re
import sys
from unittest import mock

import pytest
from dagster import AssetSelection, Definitions, asset, define_asset_job
from dagster._core.errors import DagsterInvalidSubsetError


@pytest.fixture(
    name="string_similarity_package",
    params=["difflib", "rapidfuzz"],
    ids=["no difflib", "no rapidfuzz"],
    autouse=True,
)
def uninstall_string_similarity_package_fixture(request: pytest.FixtureRequest):
    with mock.patch.dict(sys.modules, {request.param: None}):
        yield


@pytest.mark.parametrize("group_name", [None, "my_group"])
@pytest.mark.parametrize("asset_key_prefix", [[], ["my_prefix"]])
def test_typo_asset_selection_one_similar(group_name, asset_key_prefix) -> None:
    @asset(group_name=group_name, key_prefix=asset_key_prefix)
    def asset1(): ...

    my_job = define_asset_job(
        "my_job", selection=AssetSelection.assets(asset_key_prefix + ["asst1"])
    )

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())}"),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_typo_asset_selection_no_similar() -> None:
    @asset
    def asset1(): ...

    my_job = define_asset_job("my_job", selection=AssetSelection.assets("not_close_to_asset1"))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(r"no AssetsDefinition objects supply these keys."),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_typo_asset_selection_many_similar() -> None:
    @asset
    def asset1(): ...

    @asset
    def assets1(): ...

    @asset
    def asst(): ...

    my_job = define_asset_job("my_job", selection=AssetSelection.assets("asst1"))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(
            rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())},"
            rf" {re.escape(assets1.key.to_string())},"
            rf" {re.escape(asst.key.to_string())}"
        ),
    ):
        defs = Definitions(assets=[asst, asset1, assets1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_typo_asset_selection_wrong_prefix() -> None:
    @asset(key_prefix=["my", "prefix"])
    def asset1(): ...

    my_job = define_asset_job("my_job", selection=AssetSelection.assets(["my", "prfix", "asset1"]))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())}"),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_typo_asset_selection_wrong_prefix_and_wrong_key() -> None:
    # In the case that the user has a typo in the key and the prefix, we don't suggest the asset since it's too different.

    @asset(key_prefix=["my", "prefix"])
    def asset1(): ...

    my_job = define_asset_job("my_job", selection=AssetSelection.assets(["my", "prfix", "asset4"]))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(r"no AssetsDefinition objects supply these keys."),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_one_off_component_prefix() -> None:
    @asset(key_prefix=["my", "prefix"])
    def asset1(): ...

    # One more component in the prefix
    my_job = define_asset_job(
        "my_job", selection=AssetSelection.assets(["my", "prefix", "nested", "asset1"])
    )

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())}"),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")

    my_job = define_asset_job("my_job", selection=AssetSelection.assets(["my", "asset1"]))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())}"),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")


def test_select_without_prefix() -> None:
    @asset(key_prefix=["my", "long", "prefix"])
    def asset1(): ...

    # Many more components in the prefix
    my_job = define_asset_job("my_job", selection=AssetSelection.assets(["asset1"]))

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=(rf"did you mean one of the following\?\n\t{re.escape(asset1.key.to_string())}"),
    ):
        defs = Definitions(assets=[asset1], jobs=[my_job])
        defs.get_job_def("my_job")
