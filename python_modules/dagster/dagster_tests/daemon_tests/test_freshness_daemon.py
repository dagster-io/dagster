import datetime
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager

import dagster as dg
import pytest
from dagster import AssetKey, DagsterEventType, DagsterInstance
from dagster._core.definitions.freshness import FreshnessPolicy, FreshnessState
from dagster._core.events import StepMaterializationData
from dagster._core.storage.dagster_run import make_new_run_id
from dagster._core.test_utils import create_test_daemon_workspace_context, freeze_time
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.freshness import FreshnessDaemon

from dagster_tests.freshness_tests.utils import create_target_from_fn_and_local_scope


@contextmanager
def setup_remote_repo(
    instance: DagsterInstance, fn: Callable, location_name: str = "foo"
) -> Iterator[IWorkspaceProcessContext]:
    with create_target_from_fn_and_local_scope(location_name, fn) as target:
        with create_test_daemon_workspace_context(
            workspace_load_target=target,
            instance=instance,
        ) as workspace_context:
            yield workspace_context


def store_mat(instance: DagsterInstance, asset_key: AssetKey, dt: datetime.datetime):
    instance.store_event(
        dg.EventLogEntry(
            error_info=None,
            user_message="",
            level="debug",
            run_id=make_new_run_id(),
            timestamp=dt.timestamp(),
            dagster_event=dg.DagsterEvent(
                DagsterEventType.ASSET_MATERIALIZATION.value,
                "nonce",
                event_specific_data=StepMaterializationData(
                    materialization=dg.AssetMaterialization(asset_key=asset_key),
                ),
            ),
        )
    )


def run_iter(daemon: FreshnessDaemon, context: IWorkspaceProcessContext):
    list(daemon.run_iteration(context))


class FreshnessDaemonTests(ABC):
    @abstractmethod
    @pytest.fixture
    def daemon_instance(self) -> Generator[dg.DagsterInstance, None, None]: ...

    @abstractmethod
    @pytest.fixture
    def freshness_daemon(self) -> FreshnessDaemon: ...

    def _assert_freshness_state(
        self,
        instance: DagsterInstance,
        asset_key: AssetKey,
        expected_state: FreshnessState,
    ):
        """Helper method to assert the freshness state of an asset."""
        freshness_state_record = instance.get_freshness_state_records([asset_key]).get(asset_key)
        assert freshness_state_record is not None
        assert freshness_state_record.freshness_state == expected_state

    def _assert_freshness_states(
        self,
        instance: DagsterInstance,
        asset_keys: list[str],
        expected_state: FreshnessState,
    ):
        """Helper method to assert the freshness state of multiple assets."""
        for asset_key in asset_keys:
            self._assert_freshness_state(instance, dg.AssetKey(asset_key), expected_state)

    def _materialize_assets(
        self,
        instance: DagsterInstance,
        asset_keys: list[str],
        materialize_time: datetime.datetime,
    ):
        """Helper method to materialize multiple assets at a given time."""
        for asset_key in asset_keys:
            store_mat(instance, dg.AssetKey(asset_key), materialize_time)

    def test_iteration_no_freshness_policies(
        self,
        daemon_instance: DagsterInstance,
        freshness_daemon: FreshnessDaemon,
    ):
        """Test that freshness daemon is no-op for assets with no freshness policies."""

        def create_defs() -> dg.Definitions:
            @dg.asset
            def asset_1():
                return 1

            @dg.asset
            def asset_2():
                return 2

            defs = dg.Definitions(assets=[asset_1, asset_2])

            return defs

        with setup_remote_repo(instance=daemon_instance, fn=create_defs) as workspace_context:
            start_time = datetime.datetime.now(datetime.timezone.utc)
            frozen_time = start_time
            with freeze_time(frozen_time):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_1"), FreshnessState.NOT_APPLICABLE
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_2"), FreshnessState.NOT_APPLICABLE
                )

    def test_iteration_single_freshness_policy(
        self,
        daemon_instance: DagsterInstance,
        freshness_daemon: FreshnessDaemon,
    ):
        """Test that freshness daemon evaluates freshness for a single asset."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=FreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(hours=24),
                    warn_window=datetime.timedelta(hours=12),
                )
            )
            def asset_with_policy():
                return 1

            @dg.asset
            def asset_without_policy():
                return 1

            defs = dg.Definitions(assets=[asset_with_policy, asset_without_policy])

            return defs

        with setup_remote_repo(instance=daemon_instance, fn=create_defs) as workspace_context:
            # We're going to iterate through the daemon as time progresses.
            # At each iteration, we should see the freshness state for asset_with_policy transition
            # UNKNOWN -> PASS (when it materializes) -> WARN -> FAIL
            # The freshness state for asset_without_policy should always be None, since it doesn't have a freshness policy.

            start_time = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            frozen_time = start_time
            with freeze_time(frozen_time):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_with_policy"), FreshnessState.UNKNOWN
                )

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_without_policy"),
                    FreshnessState.NOT_APPLICABLE,
                )

            materialize_time = frozen_time + datetime.timedelta(seconds=1)
            with freeze_time(materialize_time):
                store_mat(daemon_instance, dg.AssetKey("asset_with_policy"), materialize_time)

                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_with_policy"), FreshnessState.PASS
                )

            # Advance 12 hours and 1 second from start -> WARN
            with freeze_time(materialize_time + datetime.timedelta(hours=12, seconds=1)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_with_policy"), FreshnessState.WARN
                )

            # Advance 24 hours and 1 second from start -> FAIL
            with freeze_time(materialize_time + datetime.timedelta(hours=24, seconds=1)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_with_policy"), FreshnessState.FAIL
                )

    def test_iteration_multiple_freshness_policies(
        self,
        daemon_instance: DagsterInstance,
        freshness_daemon: FreshnessDaemon,
    ):
        """Test that freshness daemon evaluates freshness for multiple assets with different freshness policies."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=FreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(minutes=60),
                    warn_window=datetime.timedelta(minutes=30),
                )
            )
            def asset_1():
                return 1

            @dg.asset(
                freshness_policy=FreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(minutes=120),
                    warn_window=datetime.timedelta(minutes=60),
                )
            )
            def asset_2():
                return 2

            @dg.asset(
                freshness_policy=FreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(minutes=30),
                    warn_window=datetime.timedelta(minutes=15),
                )
            )
            def asset_3():
                return 3

            defs = dg.Definitions(assets=[asset_1, asset_2, asset_3])

            return defs

        with setup_remote_repo(instance=daemon_instance, fn=create_defs) as workspace_context:
            # We'll test three assets with different freshness policies:
            # asset_1: 30min warn, 60min fail
            # asset_2: 60min warn, 120min fail
            # asset_3: 15min warn, 30min fail

            asset_keys = ["asset_1", "asset_2", "asset_3"]

            start_time = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            frozen_time = start_time
            with freeze_time(frozen_time):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_states(daemon_instance, asset_keys, FreshnessState.UNKNOWN)

            materialize_time = frozen_time + datetime.timedelta(seconds=1)
            with freeze_time(materialize_time):
                self._materialize_assets(daemon_instance, asset_keys, materialize_time)
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_states(daemon_instance, asset_keys, FreshnessState.PASS)

            # Advance 20 minutes - asset_3 should be WARN, others still PASS
            with freeze_time(materialize_time + datetime.timedelta(minutes=20)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_states(
                    daemon_instance, ["asset_1", "asset_2"], FreshnessState.PASS
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_3"), FreshnessState.WARN
                )

            # Advance 35 minutes - asset_1 should be WARN, asset_3 should be FAIL, asset_2 still PASS
            with freeze_time(materialize_time + datetime.timedelta(minutes=35)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_1"), FreshnessState.WARN
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_2"), FreshnessState.PASS
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_3"), FreshnessState.FAIL
                )

            # Advance 65 minutes - asset_1 should be FAIL, asset_2 should be WARN, asset_3 still FAIL
            with freeze_time(materialize_time + datetime.timedelta(minutes=65)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_1"), FreshnessState.FAIL
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_2"), FreshnessState.WARN
                )
                self._assert_freshness_state(
                    daemon_instance, dg.AssetKey("asset_3"), FreshnessState.FAIL
                )

            # Advance 125 minutes - all assets should be FAIL
            with freeze_time(materialize_time + datetime.timedelta(minutes=125)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_states(daemon_instance, asset_keys, FreshnessState.FAIL)

    def test_iteration_multiple_materializations(
        self,
        daemon_instance: DagsterInstance,
        freshness_daemon: FreshnessDaemon,
    ):
        """Test that freshness daemon correctly evaluates freshness using the most recent materialization."""

        def create_defs() -> dg.Definitions:
            @dg.asset(
                freshness_policy=FreshnessPolicy.time_window(
                    fail_window=datetime.timedelta(minutes=60),
                    warn_window=datetime.timedelta(minutes=30),
                )
            )
            def asset_with_multiple_materializations():
                return 1

            defs = dg.Definitions(assets=[asset_with_multiple_materializations])

            return defs

        with setup_remote_repo(instance=daemon_instance, fn=create_defs) as workspace_context:
            # We'll test an asset that gets materialized multiple times
            # and verify that the daemon uses the most recent materialization

            start_time = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            frozen_time = start_time
            with freeze_time(frozen_time):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.UNKNOWN,
                )

            first_materialize_time = frozen_time + datetime.timedelta(seconds=1)
            with freeze_time(first_materialize_time):
                store_mat(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    first_materialize_time,
                )
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.PASS,
                )

            # Advance 40 minutes - should be WARN
            with freeze_time(first_materialize_time + datetime.timedelta(minutes=40)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.WARN,
                )

            # Second materialization at 45 minutes
            second_materialize_time = first_materialize_time + datetime.timedelta(minutes=45)
            with freeze_time(second_materialize_time):
                store_mat(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    second_materialize_time,
                )
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.PASS,
                )

            # Advance 20 minutes from second materialization - should still be PASS
            with freeze_time(second_materialize_time + datetime.timedelta(minutes=20)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.PASS,
                )

            # Advance 35 minutes from second materialization - should be WARN
            with freeze_time(second_materialize_time + datetime.timedelta(minutes=35)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.WARN,
                )

            # Advance 65 minutes from second materialization - should be FAIL
            with freeze_time(second_materialize_time + datetime.timedelta(minutes=65)):
                run_iter(freshness_daemon, workspace_context)

                self._assert_freshness_state(
                    daemon_instance,
                    dg.AssetKey("asset_with_multiple_materializations"),
                    FreshnessState.FAIL,
                )


class TestFreshnessDaemon(FreshnessDaemonTests):
    @pytest.fixture
    def daemon_instance(self) -> Generator[dg.DagsterInstance, None, None]:
        with dg.instance_for_test() as instance:
            yield instance

    @pytest.fixture
    def freshness_daemon(self) -> FreshnessDaemon:
        return FreshnessDaemon()
