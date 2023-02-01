import re

import pytest
from dagster import AssetIn, AssetKey, Definitions, asset
from dagster._core.errors import DagsterInvalidDefinitionError


@pytest.mark.parametrize("group_name", [None, "my_group"])
@pytest.mark.parametrize("asset_key_prefix", [[], ["my_prefix"]])
def test_typo_upstream_asset_one_similar(group_name, asset_key_prefix):
    @asset(group_name=group_name, key_prefix=asset_key_prefix)
    def asset1():
        ...

    @asset(
        group_name=group_name,
        key_prefix=asset_key_prefix,
        ins={"asst1": AssetIn(asset_key_prefix + ["asst1"])},
    )
    def asset2(asst1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asst1\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources. Did you mean one of the following\?"
            rf"\n\t{re.escape(asset1.asset_key.to_string())}"
        ),
    ):
        Definitions(assets=[asset1, asset2])


def test_typo_upstream_asset_no_similar():
    @asset
    def asset1():
        ...

    @asset
    def asset2(not_close_to_asset1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"not_close_to_asset1\".* is not produced by any of the provided asset"
            r" ops and is not one of the provided sources."
        ),
    ):
        Definitions(assets=[asset1, asset2])


def test_typo_upstream_asset_many_similar():
    @asset
    def asset1():
        ...

    @asset
    def assets1():
        ...

    @asset
    def asst():
        ...

    @asset
    def asset2(asst1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asst1\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources. Did you mean one of the following\?"
            rf"\n\t{re.escape(asst.asset_key.to_string())},"
            rf" {re.escape(asset1.asset_key.to_string())},"
            rf" {re.escape(assets1.asset_key.to_string())}"
        ),
    ):
        Definitions(assets=[asst, asset1, assets1, asset2])


def test_typo_upstream_asset_wrong_prefix():
    @asset(key_prefix=["my", "prefix"])
    def asset1():
        ...

    @asset(ins={"asset1": AssetIn(key=AssetKey(["my", "prfix", "asset1"]))})
    def asset2(asset1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asset1\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources. Did you mean one of the following\?"
            rf"\n\t{re.escape(asset1.asset_key.to_string())}"
        ),
    ):
        Definitions(assets=[asset1, asset2])


def test_typo_upstream_asset_wrong_prefix_and_wrong_key():
    # In the case that the user has a typo in the key and the prefix, we don't suggest the asset since it's too different.

    @asset(key_prefix=["my", "prefix"])
    def asset1():
        ...

    @asset(ins={"asset1": AssetIn(key=AssetKey(["my", "prfix", "asset4"]))})
    def asset2(asset1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asset4\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources."
        ),
    ):
        Definitions(assets=[asset1, asset2])


def test_one_off_component_prefix():
    @asset(key_prefix=["my", "prefix"])
    def asset1():
        ...

    # One more component in the prefix
    @asset(ins={"asset1": AssetIn(key=AssetKey(["my", "prefix", "nested", "asset1"]))})
    def asset2(asset1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asset1\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources. Did you mean one of the following\?"
            rf"\n\t{re.escape(asset1.asset_key.to_string())}"
        ),
    ):
        Definitions(assets=[asset1, asset2])

    # One fewer component in the prefix
    @asset(ins={"asset1": AssetIn(key=AssetKey(["my", "asset1"]))})
    def asset3(asset1):
        ...

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            r"Input asset .*\"asset1\".* is not produced by any of the provided asset ops and is"
            r" not one of the provided sources. Did you mean one of the following\?"
            rf"\n\t{re.escape(asset1.asset_key.to_string())}"
        ),
    ):
        Definitions(assets=[asset1, asset3])
