from datetime import timedelta

import pytest
from dagster import AssetKey, AssetsDefinition, AssetSpec, Definitions
from dagster._check import CheckError
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.freshness import (
    INTERNAL_FRESHNESS_POLICY_METADATA_KEY,
    CronFreshnessPolicy,
    InternalFreshnessPolicy,
    TimeWindowFreshnessPolicy,
)
from dagster._serdes import deserialize_value, serialize_value
from dagster_shared.serdes.utils import SerializableTimeDelta

from dagster_tests.core_tests.host_representation_tests.test_external_data import (
    _get_asset_node_snaps_from_definitions,
)


class TestTimeWindowFreshnessPolicy:
    def test_asset_decorator_with_time_window_freshness_policy(self) -> None:
        """Can we define an asset from decorator with a time window freshness policy?"""

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
        assert deserialized.fail_window == SerializableTimeDelta.from_timedelta(
            timedelta(minutes=10)
        )
        assert deserialized.warn_window == SerializableTimeDelta.from_timedelta(
            timedelta(minutes=5)
        )

    def test_asset_spec_with_time_window_freshness_policy(self) -> None:
        """Can we define an asset spec with a time window freshness policy?"""

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

    def test_attach_time_window_freshness_policy(self) -> None:
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

    def test_map_asset_specs_attach_time_window_freshness_policy(self) -> None:
        """Can we map attach_internal_freshness_policy over a selection of assets and asset specs?"""

        @asset
        def foo_asset():
            pass

        asset_specs = [foo_asset, AssetSpec(key="bar"), AssetSpec(key="baz")]
        defs: Definitions = Definitions(assets=asset_specs)

        freshness_policy = TimeWindowFreshnessPolicy.from_timedeltas(
            fail_window=timedelta(minutes=10), warn_window=timedelta(minutes=5)
        )
        mapped_defs = defs.map_resolved_asset_specs(
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

    def test_time_window_freshness_policy_fail_window_validation(self) -> None:
        with pytest.raises(CheckError):
            InternalFreshnessPolicy.time_window(fail_window=timedelta(seconds=59))

        with pytest.raises(CheckError):
            InternalFreshnessPolicy.time_window(
                fail_window=timedelta(seconds=59), warn_window=timedelta(seconds=59)
            )

        # exactly 1 minute is ok
        InternalFreshnessPolicy.time_window(fail_window=timedelta(seconds=60))
        InternalFreshnessPolicy.time_window(
            fail_window=timedelta(seconds=61), warn_window=timedelta(minutes=1)
        )

    def test_attach_time_window_freshness_policy_overwrite_existing(self) -> None:
        """Does overwrite_existing respect existing freshness policy on an asset?"""

        @asset
        def asset_no_policy():
            pass

        @asset(
            internal_freshness_policy=InternalFreshnessPolicy.time_window(
                fail_window=timedelta(hours=24)
            )
        )
        def asset_with_policy():
            pass

        defs = Definitions(assets=[asset_no_policy, asset_with_policy])

        # If no policy is attached, overwrite with new policy containing fail window of 10 minutes
        mapped_defs = defs.map_asset_specs(
            func=lambda spec: attach_internal_freshness_policy(
                spec,
                InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=10)),
                overwrite_existing=False,
            )
        )

        specs = mapped_defs.get_all_asset_specs()

        # Should see new policy applied to asset without existing policy
        spec_no_policy = next(spec for spec in specs if spec.key == AssetKey("asset_no_policy"))
        assert spec_no_policy.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY) is not None
        assert spec_no_policy.metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY] == serialize_value(
            InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=10))
        )

        spec_with_policy = next(spec for spec in specs if spec.key == AssetKey("asset_with_policy"))
        assert spec_with_policy.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY) is not None
        assert spec_with_policy.metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY] == serialize_value(
            InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))
        )


class TestCronFreshnessPolicy:
    def test_cron_freshness_policy_validation_basic(self) -> None:
        """Can we define a cron freshness policy with valid parameters?"""
        # Valid cron string and lower bound delta
        policy = InternalFreshnessPolicy.cron(
            deadline_cron="0 10 * * *",
            lower_bound_delta=timedelta(hours=1),
        )
        assert isinstance(policy, CronFreshnessPolicy)
        assert policy.deadline_cron == "0 10 * * *"
        assert policy.lower_bound_delta == timedelta(hours=1)
        assert policy.timezone == "UTC"

    def test_cron_freshness_policy_validation_with_timezone(self) -> None:
        policy = InternalFreshnessPolicy.cron(
            deadline_cron="0 10 * * *",
            lower_bound_delta=timedelta(hours=1),
            timezone="America/New_York",
        )
        assert isinstance(policy, CronFreshnessPolicy)
        assert policy.deadline_cron == "0 10 * * *"
        assert policy.lower_bound_delta == timedelta(hours=1)
        assert policy.timezone == "America/New_York"

    def test_cron_freshness_policy_validation_invalid_cron(self) -> None:
        with pytest.raises(CheckError, match="Invalid cron string"):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * * *",  # we don't support seconds resolution in the cron
                lower_bound_delta=timedelta(hours=1),
            )

    def test_cron_freshness_policy_validation_invalid_timezone(self) -> None:
        with pytest.raises(CheckError, match="Invalid IANA timezone"):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(hours=1),
                timezone="Invalid/Timezone",
            )

    def test_cron_freshness_policy_validation_lower_bound_minimum(self) -> None:
        with pytest.raises(
            CheckError, match="lower_bound_delta must be greater than or equal to 1 minute"
        ):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(seconds=59),
            )

    def test_cron_freshness_policy_validation_zero_lower_bound(self) -> None:
        with pytest.raises(
            CheckError, match="lower_bound_delta must be greater than or equal to 1 minute"
        ):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(seconds=0),
            )

    def test_cron_freshness_policy_validation_lower_bound_too_large(self) -> None:
        with pytest.raises(
            CheckError,
            match="lower_bound_delta must be less than or equal to the smallest cron interval",
        ):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(hours=25),
            )

    def test_cron_freshness_policy_validation_lower_bound_exceeds_smallest_interval(self) -> None:
        """Does the policy reject lower bound deltas that exceed the smallest cron interval?"""
        # 0 10 * * 1-5 means 10am on Monday through Friday
        # 30 hours lower bound delta will work over the weekend, but not during the week
        with pytest.raises(
            CheckError,
            match="lower_bound_delta must be less than or equal to the smallest cron interval",
        ):
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * 1-5",
                lower_bound_delta=timedelta(hours=30),
            )

    def test_cron_freshness_policy_serdes(self) -> None:
        """Can we serialize and deserialize a cron freshness policy?"""
        policy = InternalFreshnessPolicy.cron(
            deadline_cron="0 10 * * *",
            lower_bound_delta=timedelta(hours=1),
            timezone="America/New_York",
        )
        serialized = serialize_value(policy)
        deserialized = deserialize_value(serialized)
        assert isinstance(deserialized, CronFreshnessPolicy)
        assert deserialized.deadline_cron == "0 10 * * *"
        assert deserialized.lower_bound_delta == timedelta(hours=1)
        assert deserialized.timezone == "America/New_York"

    def test_cron_freshness_policy_apply_to_asset(self) -> None:
        @asset(
            internal_freshness_policy=InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(hours=1),
                timezone="UTC",
            )
        )
        def asset_with_internal_freshness_policy():
            pass

        asset_spec = asset_with_internal_freshness_policy.get_asset_spec()
        policy = asset_spec.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY)
        assert policy is not None
        deserialized = deserialize_value(policy)
        assert isinstance(deserialized, CronFreshnessPolicy)
        assert deserialized.deadline_cron == "0 10 * * *"
        assert deserialized.lower_bound_delta == timedelta(hours=1)
        assert deserialized.timezone == "UTC"

    def test_cron_freshness_policy_apply_to_asset_spec(self) -> None:
        """Can we apply a cron freshness policy to an asset spec?"""
        asset_spec = AssetSpec(
            key="foo",
            internal_freshness_policy=InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(hours=1),
            ),
        )
        asset_spec = attach_internal_freshness_policy(
            asset_spec,
            InternalFreshnessPolicy.cron(
                deadline_cron="0 10 * * *",
                lower_bound_delta=timedelta(hours=1),
                timezone="UTC",
            ),
        )
        assert asset_spec.metadata.get(INTERNAL_FRESHNESS_POLICY_METADATA_KEY) is not None
        deserialized = deserialize_value(
            asset_spec.metadata[INTERNAL_FRESHNESS_POLICY_METADATA_KEY]
        )
        assert isinstance(deserialized, CronFreshnessPolicy)
        assert deserialized.deadline_cron == "0 10 * * *"
        assert deserialized.lower_bound_delta == timedelta(hours=1)
        assert deserialized.timezone == "UTC"
