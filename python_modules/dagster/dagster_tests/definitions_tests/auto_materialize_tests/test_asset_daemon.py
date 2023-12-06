import datetime
from contextlib import contextmanager, nullcontext
from typing import Any, Generator, Mapping, Optional, Sequence, cast

import pendulum
import pytest
from dagster import (
    AssetSpec,
    AutoMaterializeRule,
    DagsterInstance,
    instance_for_test,
)
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.automation_policy_sensor_definition import (
    AutomationPolicySensorDefinition,
)
from dagster._core.definitions.sensor_definition import DefaultSensorStatus
from dagster._core.scheduler.instigation import (
    InstigatorStatus,
    InstigatorTick,
    InstigatorType,
    SensorInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_MATERIALIZE_TAG,
    SENSOR_NAME_TAG,
)
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY,
    _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    asset_daemon_cursor_from_instigator_serialized_cursor,
    get_has_migrated_to_sensors,
    set_auto_materialize_paused,
)
from dagster._serdes.serdes import serialize_value

from .asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetDaemonScenarioState,
    AssetRuleEvaluationSpec,
)
from .base_scenario import run_request
from .updated_scenarios.asset_daemon_scenario_states import (
    one_asset,
    two_assets_in_sequence,
    two_partitions_def,
)
from .updated_scenarios.basic_scenarios import basic_scenarios
from .updated_scenarios.cron_scenarios import basic_hourly_cron_rule, get_cron_policy
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


@contextmanager
def _get_threadpool_executor(instance: DagsterInstance):
    settings = instance.get_settings("auto_materialize")
    with InheritContextThreadPoolExecutor(
        max_workers=settings.get("num_workers"),
        thread_name_prefix="asset_daemon_worker",
    ) if settings.get("use_threads") else nullcontext() as executor:
        yield executor


# just run over a subset of the total scenarios
daemon_scenarios = [*basic_scenarios, *partition_scenarios]


automation_policy_sensor_scenarios = [
    AssetDaemonScenario(
        id="basic_hourly_cron_unpartitioned",
        initial_state=one_asset.with_asset_properties(
            auto_materialize_policy=get_cron_policy(basic_hourly_cron_rule)
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A"]))
        .assert_evaluation("A", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)])
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # still no runs should be requested
        .with_current_time_advanced(minutes=50)
        .evaluate_tick()
        .assert_requested_runs()
        # moved to a new cron schedule tick, request another run
        .with_current_time_advanced(minutes=10)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A"]))
        .assert_evaluation("A", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)]),
    ),
    AssetDaemonScenario(
        id="sensor_interval_respected",
        initial_state=two_assets_in_sequence.with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]))
        .evaluate_tick()
        .assert_requested_runs()  # No runs initially
        .with_runs(run_request(["A"]))
        .evaluate_tick()
        .assert_requested_runs()  # Still no runs because no time has passed
        .with_current_time_advanced(seconds=10)  # 5 seconds later, no new tick
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(seconds=20)  # Once 30 seconds have passed, runs are created
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"])),
    ),
    AssetDaemonScenario(
        id="one_asset_never_materialized",
        initial_state=one_asset.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .assert_evaluation(
            "A", [AssetRuleEvaluationSpec(rule=AutoMaterializeRule.materialize_on_missing())]
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_already_launched",
        initial_state=one_asset.with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
]


@pytest.mark.parametrize(
    "scenario", daemon_scenarios, ids=[scenario.id for scenario in daemon_scenarios]
)
def test_asset_daemon_without_sensor(scenario: AssetDaemonScenario) -> None:
    with get_daemon_instance() as instance:
        scenario.evaluate_daemon(instance)


daemon_scenarios_with_threadpool_without_sensor = basic_scenarios[:5]


@pytest.mark.parametrize(
    "scenario",
    daemon_scenarios_with_threadpool_without_sensor,
    ids=[scenario.id for scenario in daemon_scenarios_with_threadpool_without_sensor],
)
def test_asset_daemon_with_threadpool_without_sensor(scenario: AssetDaemonScenario) -> None:
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"use_threads": True, "num_workers": 4}}
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            scenario.evaluate_daemon(instance, threadpool_executor=threadpool_executor)


@pytest.mark.parametrize(
    "scenario",
    automation_policy_sensor_scenarios,
    ids=[scenario.id for scenario in automation_policy_sensor_scenarios],
)
@pytest.mark.parametrize("num_threads", [0, 4])
def test_asset_daemon_with_sensor(scenario: AssetDaemonScenario, num_threads: int) -> None:
    with get_daemon_instance(
        extra_overrides={
            "auto_materialize": {
                "use_automation_policy_sensors": True,
                "use_threads": num_threads > 0,
                "num_workers": num_threads,
            }
        }
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            scenario.evaluate_daemon(
                instance,
                sensor_name="default_automation_policy_sensor",
                threadpool_executor=threadpool_executor,
            )


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


three_assets = AssetDaemonScenarioState(
    asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C")]
)

daemon_sensor_scenario = AssetDaemonScenario(
    id="simple_daemon_scenario",
    initial_state=three_assets.with_automation_policy_sensors(
        [
            AutomationPolicySensorDefinition(
                name="automation_policy_sensor_a",
                asset_selection=AssetSelection.keys("A"),
                default_status=DefaultSensorStatus.RUNNING,
                run_tags={
                    "foo_tag": "bar_val",
                },
            ),
            AutomationPolicySensorDefinition(
                name="automation_policy_sensor_b",
                asset_selection=AssetSelection.keys("B"),
                default_status=DefaultSensorStatus.STOPPED,
                minimum_interval_seconds=15,
            ),
            # default sensor picks up "C"
        ]
    ).with_all_eager(3),
    execution_fn=lambda state: state.evaluate_tick(),
)


def _assert_sensor_state(
    instance,
    sensor_name: str,
    expected_num_ticks: int,
    expected_status: InstigatorStatus = InstigatorStatus.RUNNING,
):
    sensor_states = [
        sensor_state
        for sensor_state in instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )
        if sensor_state.origin.instigator_name == sensor_name
    ]
    assert len(sensor_states) == 1
    sensor_state = sensor_states[0]

    assert sensor_state.status == expected_status

    ticks = instance.get_ticks(
        sensor_state.instigator_origin_id,
        sensor_state.selector_id,
    )

    assert len(ticks) == expected_num_ticks


def test_automation_policy_sensor_no_transition():
    # have not been using global AMP before - first tick does not create
    # any sensor states except for the one that is declared in code
    with get_daemon_instance(
        paused=False,
        extra_overrides={
            "auto_materialize": {
                "use_automation_policy_sensors": True,
            }
        },
    ) as instance:
        assert not get_has_migrated_to_sensors(instance)

        result = daemon_sensor_scenario.evaluate_daemon(instance)

        assert get_has_migrated_to_sensors(instance)

        sensor_states = instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )

        assert len(sensor_states) == 1
        _assert_sensor_state(
            instance,
            "automation_policy_sensor_a",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.DECLARED_IN_CODE,
        )

        # new sensor started with an empty cursor, reached evaluation ID 1
        assert (
            asset_daemon_cursor_from_instigator_serialized_cursor(
                cast(SensorInstigatorData, sensor_states[0].instigator_data).cursor,
                None,
            ).evaluation_id
            == 1
        )
        result = result.with_current_time_advanced(seconds=30)
        result = result.evaluate_tick()
        daemon_sensor_scenario.evaluate_daemon(instance)
        sensor_states = instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )
        assert len(sensor_states) == 1
        _assert_sensor_state(
            instance,
            "automation_policy_sensor_a",
            expected_num_ticks=2,
            expected_status=InstigatorStatus.DECLARED_IN_CODE,
        )
        # now on evaluation ID 2
        assert (
            asset_daemon_cursor_from_instigator_serialized_cursor(
                cast(SensorInstigatorData, sensor_states[0].instigator_data).cursor,
                None,
            ).evaluation_id
            == 2
        )


def test_automation_policy_sensor_transition():
    with get_daemon_instance(
        paused=False,
        extra_overrides={
            "auto_materialize": {
                "use_automation_policy_sensors": True,
            }
        },
    ) as instance:
        # Have been using global AMP, so there is a cursor
        pre_sensor_evaluation_id = 12345

        assert not get_has_migrated_to_sensors(instance)

        instance.daemon_cursor_storage.set_cursor_values(
            {
                _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(
                    AssetDaemonCursor.empty()._replace(evaluation_id=pre_sensor_evaluation_id)
                )
            }
        )

        # Since the global pause setting was off, all the sensors are running
        daemon_sensor_scenario.evaluate_daemon(instance)

        assert get_has_migrated_to_sensors(instance)

        sensor_states = instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )

        assert len(sensor_states) == 3  # sensor states for each sensor were created

        # Only sensor that was set with default status RUNNING turned on and ran
        _assert_sensor_state(
            instance,
            "automation_policy_sensor_a",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.DECLARED_IN_CODE,
        )
        _assert_sensor_state(
            instance,
            "automation_policy_sensor_b",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.RUNNING,
        )
        _assert_sensor_state(
            instance,
            "default_automation_policy_sensor",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.RUNNING,
        )

        for sensor_state in sensor_states:
            # cursor was propagated to each sensor, so all subsequent evaluation IDs are higher
            assert (
                asset_daemon_cursor_from_instigator_serialized_cursor(
                    cast(SensorInstigatorData, sensor_state.instigator_data).cursor,
                    None,
                ).evaluation_id
                > pre_sensor_evaluation_id
            )


@pytest.mark.parametrize("num_threads", [0, 4])
def test_automation_policy_sensor_ticks(num_threads):
    with get_daemon_instance(
        paused=True,
        extra_overrides={
            "auto_materialize": {
                "use_automation_policy_sensors": True,
                "use_threads": num_threads > 0,
                "num_workers": num_threads,
            }
        },
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            pre_sensor_evaluation_id = 12345

            instance.daemon_cursor_storage.set_cursor_values(
                {
                    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(
                        AssetDaemonCursor.empty()._replace(evaluation_id=pre_sensor_evaluation_id)
                    )
                }
            )

            # Global pause setting ignored by sensors, but per-sensor status is not ignored
            result = daemon_sensor_scenario.evaluate_daemon(
                instance, threadpool_executor=threadpool_executor
            )

            sensor_states = instance.schedule_storage.all_instigator_state(
                instigator_type=InstigatorType.SENSOR
            )

            assert len(sensor_states) == 3  # sensor states for each sensor were created

            # Only sensor that was set with default status RUNNING turned on and ran
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=1,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_b",
                expected_num_ticks=0,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "default_automation_policy_sensor",
                expected_num_ticks=0,
                expected_status=InstigatorStatus.STOPPED,
            )

            runs = instance.get_runs()

            assert len(runs) == 1
            run = runs[0]
            assert run.tags[AUTO_MATERIALIZE_TAG] == "true"
            assert run.tags["foo_tag"] == "bar_val"
            assert run.tags[SENSOR_NAME_TAG] == "automation_policy_sensor_a"
            assert int(run.tags[ASSET_EVALUATION_ID_TAG]) > pre_sensor_evaluation_id

            # Starting a sensor causes it to make ticks too
            result = result.start_sensor("automation_policy_sensor_b")
            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()
            sensor_states = instance.schedule_storage.all_instigator_state(
                instigator_type=InstigatorType.SENSOR
            )
            assert len(sensor_states) == 3

            # No new tick yet for A since only 15 seconds have passed
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=1,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "automation_policy_sensor_b", expected_num_ticks=1)

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=2,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "automation_policy_sensor_b", expected_num_ticks=2)

            # Starting a default sensor causes it to make ticks too
            result = result.start_sensor("default_automation_policy_sensor")
            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            sensor_states = instance.schedule_storage.all_instigator_state(
                instigator_type=InstigatorType.SENSOR
            )

            assert len(sensor_states) == 3
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=2,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "automation_policy_sensor_b", expected_num_ticks=3)
            _assert_sensor_state(instance, "default_automation_policy_sensor", expected_num_ticks=1)

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=3,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "automation_policy_sensor_b", expected_num_ticks=4)
            _assert_sensor_state(instance, "default_automation_policy_sensor", expected_num_ticks=1)

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=3,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "automation_policy_sensor_b", expected_num_ticks=5)
            _assert_sensor_state(instance, "default_automation_policy_sensor", expected_num_ticks=2)

            # Stop each sensor, ticks stop too
            result = result.stop_sensor("automation_policy_sensor_b")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(instance, "default_automation_policy_sensor", expected_num_ticks=3)

            result = result.stop_sensor("automation_policy_sensor_a")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(instance, "default_automation_policy_sensor", expected_num_ticks=4)

            result = result.stop_sensor("default_automation_policy_sensor")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "automation_policy_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "automation_policy_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "default_automation_policy_sensor",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.STOPPED,
            )

            seen_evaluation_ids = set()

            # Assert every tick has a unique evaluation ID, all are distinct, all are greater
            # than the pre-sensor evaluation ID and they are increasing for each sensor
            sensor_states = [
                sensor_state
                for sensor_state in instance.schedule_storage.all_instigator_state(
                    instigator_type=InstigatorType.SENSOR
                )
            ]

            for sensor_state in sensor_states:
                ticks = instance.get_ticks(
                    sensor_state.instigator_origin_id,
                    sensor_state.selector_id,
                )

                prev_evaluation_id = None
                for tick in ticks:
                    evaluation_id = tick.tick_data.auto_materialize_evaluation_id
                    assert evaluation_id > pre_sensor_evaluation_id
                    assert evaluation_id not in seen_evaluation_ids
                    seen_evaluation_ids.add(evaluation_id)
                    assert prev_evaluation_id is None or prev_evaluation_id > evaluation_id
                    prev_evaluation_id = evaluation_id


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
