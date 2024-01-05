import datetime
from contextlib import contextmanager
from typing import Any, Generator, Mapping, Optional, Sequence

import pendulum
import pytest
from dagster import DagsterInstance, instance_for_test
from dagster._core.scheduler.instigation import (
    InstigatorTick,
    InstigatorType,
    TickData,
    TickStatus,
)
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    set_auto_materialize_paused,
)

from dagster_tests.definitions_tests.auto_materialize_tests.asset_daemon_scenario import (
    AssetDaemonScenario,
)

from .updated_scenarios.asset_daemon_scenario_states import (
    two_assets_in_sequence,
    two_partitions_def,
)
from .updated_scenarios.basic_scenarios import basic_scenarios
from .updated_scenarios.partition_scenarios import partition_scenarios


@contextmanager
def get_daemon_instance(
    paused: bool = False,
    extra_overrides: Optional[Mapping[str, Any]] = None,
) -> Generator[DagsterInstance, None, None]:
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                "class": "SyncInMemoryRunLauncher",
            },
            **(extra_overrides or {}),
        }
    ) as instance:
        set_auto_materialize_paused(instance, paused)
        yield instance


# just run over a subset of the total scenarios
daemon_scenarios = [*basic_scenarios, *partition_scenarios]


@pytest.mark.parametrize(
    "scenario", daemon_scenarios, ids=[scenario.id for scenario in daemon_scenarios]
)
def test_asset_daemon(scenario: AssetDaemonScenario) -> None:
    with get_daemon_instance() as instance:
        scenario.evaluate_daemon(instance)


def _get_asset_daemon_ticks(instance: DagsterInstance) -> Sequence[InstigatorTick]:
    """Returns the set of ticks created by the asset daemon for the given instance."""
    return sorted(
        instance.get_ticks(
            origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        ),
        key=lambda tick: tick.tick_id,
    )


def _create_tick(instance: DagsterInstance, status: TickStatus, timestamp: float) -> InstigatorTick:
    return instance.create_tick(
        TickData(
            instigator_origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            instigator_name=_PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
            instigator_type=InstigatorType.AUTO_MATERIALIZE,
            status=status,
            timestamp=timestamp,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
            run_ids=[],
        )
    )


# simple scenario to test the daemon in some more exotic states. does not make any assertions
# as this state will be evaluated multiple times on the same instance and therefore assertions
# valid at the start may not be valid when repeated.
daemon_scenario = AssetDaemonScenario(
    id="simple_daemon_scenario",
    initial_state=two_assets_in_sequence.with_asset_properties(
        partitions_def=two_partitions_def
    ).with_all_eager(2),
    execution_fn=lambda state: state.evaluate_tick(),
)


def test_daemon_paused() -> None:
    with get_daemon_instance(paused=True) as instance:
        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 0

        # Daemon paused, so no ticks
        state = daemon_scenario.evaluate_daemon(instance)
        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 0

        set_auto_materialize_paused(instance, False)

        state = daemon_scenario._replace(initial_state=state).evaluate_daemon(instance)
        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[0]
        assert ticks[0].status == TickStatus.SUCCESS
        assert ticks[0].timestamp == state.current_time.timestamp()
        assert ticks[0].tick_data.end_timestamp == state.current_time.timestamp()
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

        state = daemon_scenario._replace(initial_state=state).evaluate_daemon(instance)
        ticks = _get_asset_daemon_ticks(instance)

        # no new runs, so tick is now skipped
        assert len(ticks) == 2
        assert ticks[-1].status == TickStatus.SKIPPED
        assert ticks[-1].timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2


def test_default_purge() -> None:
    with get_daemon_instance() as instance:
        scenario_time = daemon_scenario.initial_state.current_time
        _create_tick(
            instance, TickStatus.SKIPPED, (scenario_time - datetime.timedelta(days=8)).timestamp()
        )
        tick_1 = _create_tick(
            instance, TickStatus.SKIPPED, (scenario_time - datetime.timedelta(days=6)).timestamp()
        )
        tick_2 = _create_tick(
            instance, TickStatus.SKIPPED, (scenario_time - datetime.timedelta(days=1)).timestamp()
        )

        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 3

        state = daemon_scenario.evaluate_daemon(instance)

        # creates one SUCCESS tick and purges the old SKIPPED tick
        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 3

        assert ticks[-1].status == TickStatus.SUCCESS
        assert ticks[-1].timestamp == state.current_time.timestamp()

        assert ticks[0] == tick_1
        assert ticks[1] == tick_2


def test_custom_purge() -> None:
    with get_daemon_instance(
        extra_overrides={"retention": {"auto_materialize": {"purge_after_days": {"skipped": 2}}}},
    ) as instance:
        freeze_datetime = pendulum.now("UTC")

        _create_tick(instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=8).timestamp())
        _create_tick(instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=6).timestamp())
        tick_1 = _create_tick(
            instance, TickStatus.SKIPPED, freeze_datetime.subtract(days=1).timestamp()
        )

        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 3

        # creates one SUCCESS tick and purges the old SKIPPED ticks
        state = daemon_scenario.evaluate_daemon(instance)
        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 2

        assert ticks[-1]
        assert ticks[-1].status == TickStatus.SUCCESS
        assert ticks[-1].timestamp == state.current_time.timestamp()

        assert ticks[0] == tick_1


def test_custom_run_tags() -> None:
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"run_tags": {"foo": "bar"}}}
    ) as instance:
        daemon_scenario.evaluate_daemon(instance)

        runs = instance.get_runs()
        for run in runs:
            assert run.tags["foo"] == "bar"
