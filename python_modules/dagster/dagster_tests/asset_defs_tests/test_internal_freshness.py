from datetime import timedelta

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec, attach_internal_freshness_policy
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.freshness import (
    INTERNAL_FRESHNESS_POLICY_METADATA_KEY,
    TimeWindowFreshnessPolicy,
)
from dagster._serdes import deserialize_value
from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster_tests.core_tests.host_representation_tests.test_external_data import (
    _get_asset_node_snaps_from_definitions,
)


def test_asset_spec_with_internal_freshness_policy() -> None:
    """Can we define an asset spec with an internal freshness policy?"""

    def create_spec_and_verify_policy(asset_key: str, fail_window: timedelta, warn_window=None):
        asset = AssetSpec(
            key=AssetKey(asset_key),
            internal_freshness_policy=TimeWindowFreshnessPolicy.from_timedeltas(
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
        TimeWindowFreshnessPolicy.from_timedeltas(
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
        asset_spec, TimeWindowFreshnessPolicy.from_timedeltas(fail_window=timedelta(minutes=60))
    )
    assert_freshness_policy(asset_spec, expected_fail_window=timedelta(minutes=60))


def test_map_asset_specs_attach_internal_freshness_policy() -> None:
    """Can we map attach_internal_freshness_policy over a selection of asset specs?"""
    asset_specs = [AssetSpec(key="foo"), AssetSpec(key="bar"), AssetSpec(key="baz")]
    freshness_policy = TimeWindowFreshnessPolicy.from_timedeltas(
        fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
    )
    defs: Definitions = Definitions(assets=asset_specs)
    mapped_defs = defs.map_asset_specs(
        func=lambda spec: attach_internal_freshness_policy(spec, freshness_policy)
    )

    assets = mapped_defs.assets
    assert len(assets) == 3
    for asset in assets:
        assert INTERNAL_FRESHNESS_POLICY_METADATA_KEY in asset.metadata
        policy = deserialize_value(asset.metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY])
        assert isinstance(policy, TimeWindowFreshnessPolicy)
        assert policy.fail_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=10))
        assert policy.warn_window == SerializableTimeDelta.from_timedelta(timedelta(minutes=5))
