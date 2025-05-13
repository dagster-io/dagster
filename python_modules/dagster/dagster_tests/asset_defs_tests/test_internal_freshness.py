from datetime import timedelta

import pytest
from dagster._check import CheckError
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec, attach_internal_freshness_policy
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness import (
    INTERNAL_FRESHNESS_POLICY_METADATA_KEY,
    InternalFreshnessPolicy,
    TimeWindowFreshnessPolicy,
)
from dagster._serdes import deserialize_value
from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster_tests.core_tests.host_representation_tests.test_external_data import (
    _get_asset_node_snaps_from_definitions,
)


def test_asset_decorator_with_internal_freshness_policy() -> None:
    """Can we define an asset from decorator with an internal freshness policy?"""

    @asset(
        internal_freshness_policy=TimeWindowFreshnessPolicy.from_timedeltas(
            fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
        )
    )
    def asset_with_internal_freshness_policy():
        pass

    spec = asset_with_internal_freshness_policy.get_asset_spec()
    policy = spec.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY)
    assert policy is not None
    deserialized = deserialize_value(policy)
    assert isinstance(deserialized, TimeWindowFreshnessPolicy)
    assert deserialized.fail_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=10))
    assert deserialized.warn_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=5))


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

    # Test without warn window
    create_spec_and_verify_policy("asset1", fail_window=timedelta(minutes=10))

    # Test with optional warn window
    create_spec_and_verify_policy(
        "asset2", fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )


def test_attach_internal_freshness_policy() -> None:
    """Can we attach an internal freshness policy to an asset spec?"""

    def assert_freshness_policy(spec, expected_fail_window, expected_warn_window=None):
        metadata = spec.metadata
        assert INTERNAL_FRESHNESS_POLICY_METADATA_KEY in metadata
        deserialized = deserialize_value(metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY])
        assert isinstance(deserialized, TimeWindowFreshnessPolicy)
        assert deserialized.fail_window == SerializableTimeDelta.from_timedelta(
            expected_fail_window
        )
        if expected_warn_window:
            assert deserialized.warn_window == SerializableTimeDelta.from_timedelta(
                expected_warn_window
            )
        else:
            assert deserialized.warn_window is None

    asset_spec = AssetSpec(key="foo")
    asset_spec = attach_internal_freshness_policy(
        asset_spec,
        InternalFreshnessPolicy.time_window(
            fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
        ),
    )
    assert_freshness_policy(
        asset_spec,
        expected_fail_window=timedelta(minutes=10),
        expected_warn_window=timedelta(minutes=5),
    )

    # Overwrite the policy with a new one
    asset_spec = attach_internal_freshness_policy(
        asset_spec, InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=60))
    )
    assert_freshness_policy(asset_spec, expected_fail_window=timedelta(minutes=60))

    # Don't overwrite existing metadata
    spec_with_metadata = AssetSpec(key="bar", metadata={"existing": "metadata"})
    spec_with_metadata = attach_internal_freshness_policy(
        spec_with_metadata,
        InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=60)),
    )
    assert spec_with_metadata.metadata.get("existing") == "metadata"
    assert_freshness_policy(
        spec_with_metadata,
        expected_fail_window=timedelta(minutes=60),
        expected_warn_window=None,
    )


def test_map_asset_specs_attach_internal_freshness_policy() -> None:
    """Can we map attach_internal_freshness_policy over a selection of assets and asset specs?"""

    @asset
    def foo_asset():
        pass

    asset_specs = [foo_asset, AssetSpec(key="bar"), AssetSpec(key="baz")]
    defs: Definitions = Definitions(assets=asset_specs)

    freshness_policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )
    mapped_defs = defs.map_asset_specs(
        func=lambda spec: attach_internal_freshness_policy(spec, freshness_policy)
    )

    assets_and_specs = mapped_defs.assets
    assert assets_and_specs is not None
    for asset_or_spec in assets_and_specs:
        assert isinstance(asset_or_spec, (AssetsDefinition, AssetSpec))
        spec = (
            asset_or_spec.get_asset_spec()
            if isinstance(asset_or_spec, AssetsDefinition)
            else asset_or_spec
        )
        assert INTERNAL_FRESHNESS_POLICY_METADATA_KEY in spec.metadata
        policy = deserialize_value(spec.metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY])
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=10))
        assert policy.warn_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=5))


def test_internal_freshness_policy_fail_window_validation() -> None:
    with pytest.raises(CheckError):
        InternalFreshnessPolicy.time_window(fail_window=timedelta(seconds=59))

    with pytest.raises(CheckError):
        InternalFreshnessPolicy.time_window(
            fail_window=timedelta(seconds=59), warn_window=timedelta(seconds=59)
        )

    # exactly 1 minute is ok
    InternalFreshnessPolicy.time_window(
        fail_window=timedelta(seconds=61), warn_window=timedelta(minutes=1)
    )
