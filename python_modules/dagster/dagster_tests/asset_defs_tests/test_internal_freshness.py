from collections.abc import Iterable
from datetime import timedelta
from typing import Union

import pytest
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec, apply_internal_freshness_policy
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness import (
    INTERNAL_FRESHNESS_POLICY_METADATA_KEY,
    InternalFreshnessPolicy,
    TimeWindowFreshnessPolicy,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._serdes import deserialize_value
from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster_tests.core_tests.host_representation_tests.test_external_data import (
    _get_asset_node_snaps_from_definitions,
)


def assert_time_window_policy_on_asset(
    policy: InternalFreshnessPolicy, asset: Union[AssetSpec, AssetsDefinition]
) -> None:
    spec = asset.get_asset_spec() if isinstance(asset, AssetsDefinition) else asset
    serialized_policy = spec.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY)
    assert serialized_policy is not None
    deserialized = deserialize_value(serialized_policy)
    assert isinstance(deserialized, TimeWindowFreshnessPolicy)
    assert deserialized.fail_window == policy.fail_window
    assert deserialized.warn_window == policy.warn_window


def assert_time_window_policy_on_assets(
    policy: InternalFreshnessPolicy, assets: Iterable[Union[AssetSpec, AssetsDefinition]]
) -> None:
    for a in assets:
        assert_time_window_policy_on_asset(policy, a)


def test_asset_decorator_with_internal_freshness_policy() -> None:
    """Can we define an asset from decorator with an internal freshness policy?"""
    policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )

    @asset(internal_freshness_policy=policy)
    def asset_with_internal_freshness_policy():
        pass

    assert_time_window_policy_on_asset(policy, asset_with_internal_freshness_policy)


def test_asset_spec_with_internal_freshness_policy() -> None:
    """Can we define an asset spec with an internal freshness policy?"""

    def create_spec_and_verify_policy(asset_key: str, fail_window: timedelta, warn_window=None):
        asset = AssetSpec(
            key=AssetKey(asset_key),
            internal_freshness_policy=InternalFreshnessPolicy.time_window(
                fail_window=fail_window, warn_window=warn_window
            ),
        )

        asset_node_snaps = _get_asset_node_snaps_from_definitions(Definitions(assets=[asset]))
        snap = asset_node_snaps[0]
        policy = snap.internal_freshness_policy
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window == SerializableTimeDelta.from_timedelta(fail_window)
        if warn_window:
            assert policy.warn_window == SerializableTimeDelta.from_timedelta(warn_window)
        else:
            assert policy.warn_window is None

    create_spec_and_verify_policy("asset1", fail_window=timedelta(minutes=10))

    create_spec_and_verify_policy(
        "asset2", fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )


def test_apply_internal_freshness_policy_multiple_assets() -> None:
    """Can we apply internal freshness policy to multiple assets?"""

    @asset
    def foo_asset():
        pass

    asset_specs = [foo_asset, AssetSpec(key="bar"), AssetSpec(key="baz")]

    freshness_policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )

    mapped_assets = apply_internal_freshness_policy(freshness_policy, asset_specs)

    assert_time_window_policy_on_assets(freshness_policy, mapped_assets)


def test_apply_internal_freshness_policy_unsupported_types() -> None:
    """Applying freshness policy to unsupported types should raise ValueError by default."""

    @asset
    def foo_asset():
        pass

    foo_spec = AssetSpec(key="foo_spec")
    foo_source_asset = SourceAsset(key="foo_source_asset")

    assets = [foo_asset, foo_spec, foo_source_asset]

    freshness_policy = InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )

    with pytest.raises(ValueError, match="All assets must be AssetSpec or AssetsDefinition"):
        apply_internal_freshness_policy(freshness_policy, assets)


def test_apply_internal_freshness_policy_skip_unsupported() -> None:
    """Test that skip_unsupported=True preserves unsupported assets and only applies policy to supported ones."""

    @asset
    def foo_asset():
        pass

    foo_spec = AssetSpec(key="foo_spec")
    foo_source_asset = SourceAsset(key="foo_source_asset")

    assets = [foo_asset, foo_spec, foo_source_asset]

    freshness_policy = InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )

    mapped_assets = apply_internal_freshness_policy(freshness_policy, assets, skip_unsupported=True)

    assert len(mapped_assets) == len(assets)

    for asset_or_spec in mapped_assets:
        if isinstance(asset_or_spec, (AssetsDefinition, AssetSpec)):
            assert_time_window_policy_on_asset(freshness_policy, asset_or_spec)
        else:
            assert isinstance(asset_or_spec, SourceAsset)
            assert asset_or_spec.key == AssetKey("foo_source_asset")


def test_apply_internal_freshness_policy_overwrite_existing() -> None:
    """Test that applying a freshness policy overwrites any existing policies."""

    @asset(
        internal_freshness_policy=TimeWindowFreshnessPolicy.from_timedeltas(
            fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
        )
    )
    def asset_with_policy():
        pass

    spec_with_policy = AssetSpec(
        key="spec_with_policy_1",
        internal_freshness_policy=InternalFreshnessPolicy.time_window(
            fail_window=timedelta(minutes=30), warn_window=timedelta(minutes=25)
        ),
    )

    assets = [asset_with_policy, spec_with_policy]

    new_policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(minutes=60), warn_window=timedelta(minutes=55)
    )

    mapped_assets = apply_internal_freshness_policy(new_policy, assets)

    assert_time_window_policy_on_assets(new_policy, mapped_assets)


def test_apply_internal_freshness_policy_preserves_metadata() -> None:
    """Test that applying an internal freshness policy preserves existing metadata."""

    @asset(metadata={"decorated_asset_metadata": "value"})
    def decorated_asset():
        pass

    spec_with_metadata = AssetSpec(key="bar", metadata={"asset_spec": "metadata"})

    freshness_policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(hours=48), warn_window=timedelta(hours=24)
    )

    mapped_assets = apply_internal_freshness_policy(
        freshness_policy, [spec_with_metadata, decorated_asset]
    )

    assert_time_window_policy_on_assets(freshness_policy, mapped_assets)

    mapped_spec = mapped_assets[0]
    assert isinstance(mapped_spec, AssetSpec)
    assert mapped_spec.metadata.get("asset_spec") == "metadata"

    mapped_asset_from_decorator = mapped_assets[1]
    assert isinstance(mapped_asset_from_decorator, AssetsDefinition)
    assert (
        mapped_asset_from_decorator.get_asset_spec().metadata.get("decorated_asset_metadata")
        == "value"
    )
