import dataclasses
import datetime
from contextlib import contextmanager, nullcontext
from typing import Any, Generator, Mapping, Optional, Sequence, cast

import pytest
from dagster import (
    AssetSpec,
    AutoMaterializeRule,
    AutomationCondition,
    DagsterInstance,
    instance_for_test,
)
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
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
    AUTOMATION_CONDITION_TAG,
    SENSOR_NAME_TAG,
    TICK_ID_TAG,
)
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._daemon.asset_daemon import (
    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY,
    _PRE_SENSOR_AUTO_MATERIALIZE_INSTIGATOR_NAME,
    _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
    _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
    asset_daemon_cursor_from_instigator_serialized_cursor,
    get_has_migrated_sensor_names,
    get_has_migrated_to_sensors,
    set_auto_materialize_paused,
)
from dagster._serdes.serdes import deserialize_value, serialize_value
from dagster._time import get_current_datetime, get_current_timestamp

from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.updated_scenarios.basic_scenarios import (
    basic_scenarios,
)
from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.updated_scenarios.cron_scenarios import (
    basic_hourly_cron_rule,
    basic_hourly_cron_schedule,
    get_cron_policy,
)
from dagster_tests.definitions_tests.declarative_automation_tests.legacy_tests.updated_scenarios.partition_scenarios import (
    partition_scenarios,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetRuleEvaluationSpec,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.base_scenario import (
    run_request,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_specs import (
    one_asset,
    one_upstream_observable_asset,
    two_assets_in_sequence,
    two_partitions_def,
)
from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state import (
    ScenarioSpec,
    get_code_location_origin,
)


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


# Additional repo with assets that should be not be included in the evaluation
extra_definitions = ScenarioSpec(
    [
        AssetSpec("extra_asset1", auto_materialize_policy=AutoMaterializePolicy.eager()),
        AssetSpec(
            "extra_asset2",
            deps=["extra_asset1"],
            auto_materialize_policy=AutoMaterializePolicy.eager(),
        ),
    ]
)

other_repo_definitions = ScenarioSpec(
    asset_specs=[AssetSpec("asset1", auto_materialize_policy=AutoMaterializePolicy.eager())]
)


second_asset_in_our_repo = ScenarioSpec(
    asset_specs=[AssetSpec("asset2", deps=["asset1"])]
).with_additional_repositories([other_repo_definitions])


cross_repo_sensor_scenario = AssetDaemonScenario(
    id="two_cross_repo_assets",
    initial_spec=second_asset_in_our_repo.with_all_eager(),
    # No runs since the first asset is not yet materialized and is not being considered by this sensor
    execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(),
)


auto_materialize_sensor_scenarios = [
    cross_repo_sensor_scenario,
    AssetDaemonScenario(
        id="basic_hourly_cron_unpartitioned",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule)
        )
        .with_current_time("2020-01-01T00:05")
        .with_additional_repositories([extra_definitions]),
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
        initial_spec=two_assets_in_sequence.with_all_eager().with_additional_repositories(
            [extra_definitions]
        ),
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
        initial_spec=one_asset.with_all_eager().with_additional_repositories([extra_definitions]),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .assert_evaluation(
            "A", [AssetRuleEvaluationSpec(rule=AutoMaterializeRule.materialize_on_missing())]
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_already_launched",
        initial_spec=one_asset.with_all_eager().with_additional_repositories([extra_definitions]),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="one_upstream_observable_asset",
        initial_spec=one_upstream_observable_asset.with_asset_properties(
            automation_condition=AutomationCondition.cron_tick_passed("*/10 * * * *"),
        ),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(minutes=10)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B"])),
    ),
]


@pytest.mark.parametrize(
    "scenario", daemon_scenarios, ids=[scenario.id for scenario in daemon_scenarios]
)
def test_asset_daemon_without_sensor(scenario: AssetDaemonScenario) -> None:
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"use_sensors": False}}
    ) as instance:
        scenario.evaluate_daemon(instance)


daemon_scenarios_with_threadpool_without_sensor = basic_scenarios[:5]


@pytest.mark.parametrize(
    "scenario",
    daemon_scenarios_with_threadpool_without_sensor,
    ids=[scenario.id for scenario in daemon_scenarios_with_threadpool_without_sensor],
)
def test_asset_daemon_with_threadpool_without_sensor(
    scenario: AssetDaemonScenario,
) -> None:
    with get_daemon_instance(
        extra_overrides={
            "auto_materialize": {"use_threads": True, "num_workers": 4, "use_sensors": False}
        }
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            scenario.evaluate_daemon(instance, threadpool_executor=threadpool_executor)


@pytest.mark.parametrize(
    "scenario",
    auto_materialize_sensor_scenarios,
    ids=[scenario.id for scenario in auto_materialize_sensor_scenarios],
)
@pytest.mark.parametrize("num_threads", [0, 4])
def test_asset_daemon_with_sensor(scenario: AssetDaemonScenario, num_threads: int) -> None:
    with get_daemon_instance(
        extra_overrides={
            "auto_materialize": {
                "use_threads": num_threads > 0,
                "num_workers": num_threads,
            }
        }
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            scenario.evaluate_daemon(
                instance,
                sensor_name="default_automation_condition_sensor",
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
    initial_spec=two_assets_in_sequence.with_asset_properties(
        partitions_def=two_partitions_def
    ).with_all_eager(2),
    execution_fn=lambda state: state.evaluate_tick(),
)


def test_daemon_paused() -> None:
    with get_daemon_instance(
        paused=True, extra_overrides={"auto_materialize": {"use_sensors": False}}
    ) as instance:
        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 0

        # Daemon paused, so no ticks
        state = daemon_scenario.evaluate_daemon(instance)
        ticks = _get_asset_daemon_ticks(instance)
        assert len(ticks) == 0

        set_auto_materialize_paused(instance, False)

        state = daemon_scenario.execution_fn(state)
        ticks = _get_asset_daemon_ticks(instance)

        assert len(ticks) == 1
        assert ticks[0]
        assert ticks[0].status == TickStatus.SUCCESS
        assert ticks[0].timestamp == state.current_time.timestamp()
        assert ticks[0].tick_data.end_timestamp == state.current_time.timestamp()
        assert ticks[0].tick_data.auto_materialize_evaluation_id == 1

        state = daemon_scenario.execution_fn(state)
        ticks = _get_asset_daemon_ticks(instance)

        # no new runs, so tick is now skipped
        assert len(ticks) == 2
        assert ticks[-1].status == TickStatus.SKIPPED
        assert ticks[-1].timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.end_timestamp == state.current_time.timestamp()
        assert ticks[-1].tick_data.auto_materialize_evaluation_id == 2


three_assets = ScenarioSpec(asset_specs=[AssetSpec("A"), AssetSpec("B"), AssetSpec("C")])

daemon_sensor_scenario = AssetDaemonScenario(
    id="simple_daemon_scenario",
    initial_spec=three_assets.with_sensors(
        [
            AutomationConditionSensorDefinition(
                name="auto_materialize_sensor_a",
                asset_selection=AssetSelection.assets("A"),
                default_status=DefaultSensorStatus.RUNNING,
                run_tags={
                    "foo_tag": "bar_val",
                },
            ),
            AutomationConditionSensorDefinition(
                name="auto_materialize_sensor_b",
                asset_selection=AssetSelection.assets("B"),
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


def test_auto_materialize_sensor_no_transition():
    # have not been using global AMP before - first tick does not create
    # any sensor states except for the one that is declared in code
    with get_daemon_instance(paused=False) as instance:
        assert not get_has_migrated_to_sensors(instance)

        result = daemon_sensor_scenario.evaluate_daemon(instance)

        assert get_has_migrated_to_sensors(instance)

        sensor_states = instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )

        assert len(sensor_states) == 1
        _assert_sensor_state(
            instance,
            "auto_materialize_sensor_a",
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
            "auto_materialize_sensor_a",
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


def test_auto_materialize_sensor_transition():
    with get_daemon_instance(paused=False) as instance:
        # Have been using global AMP, so there is a cursor
        pre_sensor_evaluation_id = 4
        for _ in range(pre_sensor_evaluation_id):
            # create junk ticks so that the next tick id will be 4
            instance.create_tick(
                TickData(
                    instigator_origin_id="",
                    instigator_name="",
                    instigator_type=InstigatorType.SCHEDULE,
                    status=TickStatus.SUCCESS,
                    timestamp=get_current_timestamp(),
                    run_ids=[],
                )
            )

        assert not get_has_migrated_to_sensors(instance)

        instance.daemon_cursor_storage.set_cursor_values(
            {
                _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(
                    dataclasses.replace(
                        AssetDaemonCursor.empty(), evaluation_id=pre_sensor_evaluation_id
                    )
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
            "auto_materialize_sensor_a",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.DECLARED_IN_CODE,
        )
        _assert_sensor_state(
            instance,
            "auto_materialize_sensor_b",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.RUNNING,
        )
        _assert_sensor_state(
            instance,
            "default_automation_condition_sensor",
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


# this scenario simulates the true default case in which we have an implicit default sensor
single_daemon_sensor_scenario = AssetDaemonScenario(
    id="simplest_daemon_scenario",
    initial_spec=three_assets.with_sensors(
        [
            AutomationConditionSensorDefinition(
                name="named_sensor",
                asset_selection=AssetSelection.assets("C"),
                default_status=DefaultSensorStatus.RUNNING,
            ),
        ]
    ).with_all_eager(3),
    # advance time so that we'll have another tick immediately
    execution_fn=lambda state: state.evaluate_tick(),
)


def test_auto_materialize_sensor_name_transition() -> None:
    # this instigator state was generated from a scenario which used an automation sensor with the
    # old default name.
    instigator_state_str = """
[{"__class__": "InstigatorState", "job_specific_data": {"__class__": "SensorInstigatorData", "cursor": "0eJztmU1v1DAQhv9KlTNCjr/NrS03JC4cq8oa22MasUmWxFmoVv3vONkuLRUgBKvVGu1pN+Ox5/UzTqJX2VbW+hWMo7XVm4vqchwxvQVs++56GsZ+qF5dVLiB1QSp6TvbhJxV51iekmzvRhw2aAf8PGG+Tk2bf6BdW3dvYV7KfsL7PGObq7SwXjfdR9skbHfVbm4f8krrATdNP43W911olip+KT3OKdsX+qbUt4uU6332M50xok9NFvRdyKxW0boWrFb8tRaa6r143GCXdhvqptUqh7s+4L72vIOpa/K+dinbijgVfF1TwqgHwzxHMNGL/IcHUIo+bvP3Yt/nEk+CPeRwgIR2nDLK9JMlZogfdoN5wkumLzPf5ZEZKaS7GV51WS2I5/5hDqRhwvkav6YBbAaU8Gn3Owmj/dKkO9tigiwMli7lwXnmkURGWI34MEdYiERj1EAMwcB4cFKhCdQZ5VykoljiR+B3Qg1dGMwB7p32yCXhlGoTHRNKQwyqVl55L+pi+3myd5DSWgfppddSMkpUfgByF4UIQTiOQZ2JH5q4EZTmd42gnudHl5S1rCHo6I1hzOhozsQPTRxo8EoZY1BFyb1wXmughCtNgyb+fMYPT5wJ4ZCjERLzO5krIh0BzniESCQLZ+KHJh4N6nyiqZKUqsCIkjVSoaOLJkD0Z+KHJf6DLXk0NxiODGrAcVolu4TtHYxzcsUFi9o4CV5iBKKCFLSWYJwJgmHEKs88W6Z/6cZVCcf26n+yTH9E/Aj8TqihRVumsu+gEi1T2cRLtExlEy/RMhVOvEDLVDbxEi1TwcSPa5l+AeovLdPtc+3PPnbtid/cPnwDztf1/w==", "last_run_key": null, "last_sensor_start_timestamp": null, "last_tick_start_timestamp": null, "last_tick_timestamp": 1721153174.85828, "min_interval": 30, "sensor_type": {"__enum__": "SensorType.AUTO_MATERIALIZE"}}, "job_type": {"__enum__": "InstigatorType.SENSOR"}, "origin": {"__class__": "ExternalJobOrigin", "external_repository_origin": {"__class__": "ExternalRepositoryOrigin", "repository_location_origin": {"__class__": "InProcessRepositoryLocationOrigin", "container_context": {}, "container_image": null, "entry_point": ["dagster"], "loadable_target_origin": {"__class__": "LoadableTargetOrigin", "attribute": "_asset_daemon_target_7536c52ad38a1551adc94d1c01f57384b1f17266", "executable_path": "/Users/owen/.virtualenvs/dagster/bin/python3", "module_name": "dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state", "package_name": null, "python_file": null, "working_directory": "/Users/owen/src/dagster/js_modules/dagster-ui"}, "location_name": "test_location"}, "repository_name": "__repository__"}, "job_name": "default_auto_materialize_sensor"}, "status": {"__enum__": "InstigatorStatus.RUNNING"}}, {"__class__": "InstigatorState", "job_specific_data": {"__class__": "SensorInstigatorData", "cursor": "0eJztl01r3DAQhv9K8LkUWd/qraS3Qi89liBG0qgxXdtbS942LPnvHXuzTbqUnJaQwJ5sj2Y07zySJWbfeB83UIr3zYer5mMpWD8B9uNwPU9lnJp3Vw3uYDND7cbBd4m8ONkopPoxFJx26Cf8OSN9166nB/RbH+48LFP5H3hHEXvK0sN22w3ffVexP2T7dnNPM20n3HXjXHwch9StWeKauiwu+xN9cx37Vcr10fuJzpwx1o4E/RVCMa3hbatEa+R7qyy3R/G4w6EeChrmzYbMw5jwmHupYB46quvgsm9YMCm2LWeCR3AiSgSXo6IXmcAY/lDm82K/UIpHwRHInKCiLzOhrP+ZYoH49TBIAadMTz0/08iCFOrtAq+5blbEy/ohGeo04/KNv+sEngBVfKz+IKH4X1299T1WIGGwrhINLpEvJDLDpuD9YhEpM4vZAnMMk5ApaIMu8eBMCJmrN0v8Bfi9ogVdGSwGGYONKDWTnFuXg1DGQk6mNdHEqNo3u56v9g8y1tqko45Wa8GZoQNQhqxUSipITOZC/NzEneKc7hrFo6SjS+tWt5Bsjs4J4Wx2F+LnJg48RWOcc2iyllGFaC1wJo3lybJ42ePnJy6UCijRKY10J0vDdGAghcyQmRbpQvzcxLNDSzuaG825SYIZ3SJXNofsEuR4IX5e4v+0JQ/NDaYXBjVhmTfVr2Z/C2VxbqQS2bqgIWrMwEzSircaXHBJCczY3N881f6kczsSp6brD0jEnt0=", "last_run_key": null, "last_sensor_start_timestamp": null, "last_tick_start_timestamp": null, "last_tick_timestamp": 1721153174.85828, "min_interval": 30, "sensor_type": {"__enum__": "SensorType.AUTO_MATERIALIZE"}}, "job_type": {"__enum__": "InstigatorType.SENSOR"}, "origin": {"__class__": "ExternalJobOrigin", "external_repository_origin": {"__class__": "ExternalRepositoryOrigin", "repository_location_origin": {"__class__": "InProcessRepositoryLocationOrigin", "container_context": {}, "container_image": null, "entry_point": ["dagster"], "loadable_target_origin": {"__class__": "LoadableTargetOrigin", "attribute": "_asset_daemon_target_7536c52ad38a1551adc94d1c01f57384b1f17266", "executable_path": "/Users/owen/.virtualenvs/dagster/bin/python3", "module_name": "dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state", "package_name": null, "python_file": null, "working_directory": "/Users/owen/src/dagster/js_modules/dagster-ui"}, "location_name": "test_location"}, "repository_name": "__repository__"}, "job_name": "named_sensor"}, "status": {"__enum__": "InstigatorStatus.DECLARED_IN_CODE"}}]
"""

    # now pre-populate this instance with that modified instigator state
    with get_daemon_instance(paused=False) as instance:
        assert instance.schedule_storage is not None

        # copy over the state from the old scenario
        for state in deserialize_value(instigator_state_str, as_type=list):
            # we update the code location origin from the insitigator state string to ensure that it
            # lines up with the current-day origin
            updated_state = state._replace(
                origin=state.origin._replace(
                    repository_origin=state.origin.repository_origin._replace(
                        code_location_origin=get_code_location_origin(
                            single_daemon_sensor_scenario.initial_spec
                        )
                    )
                )
            )
            instance.schedule_storage.add_instigator_state(updated_state)
        assert not get_has_migrated_sensor_names(instance)

        # we evaluate a single tick of the renamed sensor
        single_daemon_sensor_scenario.evaluate_daemon(instance)

        assert get_has_migrated_sensor_names(instance)

        sensor_states = instance.schedule_storage.all_instigator_state(
            instigator_type=InstigatorType.SENSOR
        )

        # there are still 2 sensors, but we have some old state for "default_auto_materialize_sensor"
        assert len(sensor_states) == 3

        _assert_sensor_state(
            instance,
            "default_automation_condition_sensor",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.RUNNING,
        )
        _assert_sensor_state(
            instance,
            "named_sensor",
            expected_num_ticks=1,
            expected_status=InstigatorStatus.DECLARED_IN_CODE,
        )

        for sensor_state in sensor_states:
            # skip over the old state for the old name
            if sensor_state.instigator_name == "default_auto_materialize_sensor":
                continue
            # we do not account for the old cursor as it is assumed that the current
            # tick id will be strictly larger than the current asset daemon cursor
            # value in the real world (as each evaluation creates a new tick)
            assert (
                asset_daemon_cursor_from_instigator_serialized_cursor(
                    cast(SensorInstigatorData, sensor_state.instigator_data).cursor,
                    None,
                ).evaluation_id
                > 0  # real world should be larger
            )


@pytest.mark.parametrize("num_threads", [0, 4])
def test_auto_materialize_sensor_ticks(num_threads):
    with get_daemon_instance(
        paused=True,
        extra_overrides={
            "auto_materialize": {
                "use_threads": num_threads > 0,
                "num_workers": num_threads,
            }
        },
    ) as instance:
        with _get_threadpool_executor(instance) as threadpool_executor:
            pre_sensor_evaluation_id = 3
            for _ in range(pre_sensor_evaluation_id):
                # create junk ticks so that the next tick id will be 4
                instance.create_tick(
                    TickData(
                        instigator_origin_id="",
                        instigator_name="",
                        instigator_type=InstigatorType.SCHEDULE,
                        status=TickStatus.SUCCESS,
                        timestamp=get_current_timestamp(),
                        run_ids=[],
                    )
                )

            instance.daemon_cursor_storage.set_cursor_values(
                {
                    _PRE_SENSOR_AUTO_MATERIALIZE_CURSOR_KEY: serialize_value(
                        dataclasses.replace(
                            AssetDaemonCursor.empty(),
                            evaluation_id=pre_sensor_evaluation_id,
                        )
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
                "auto_materialize_sensor_a",
                expected_num_ticks=1,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_b",
                expected_num_ticks=0,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "default_automation_condition_sensor",
                expected_num_ticks=0,
                expected_status=InstigatorStatus.STOPPED,
            )

            runs = instance.get_runs()

            assert len(runs) == 1
            run = runs[0]
            assert run.tags[AUTO_MATERIALIZE_TAG] == "true"
            assert run.tags[AUTOMATION_CONDITION_TAG] == "true"
            assert run.tags["foo_tag"] == "bar_val"
            assert int(run.tags[ASSET_EVALUATION_ID_TAG]) > pre_sensor_evaluation_id
            assert run.tags[SENSOR_NAME_TAG] == "auto_materialize_sensor_a"

            assert int(run.tags[TICK_ID_TAG]) > 0

            # Starting a sensor causes it to make ticks too
            result = result.start_sensor("auto_materialize_sensor_b")
            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()
            sensor_states = instance.schedule_storage.all_instigator_state(
                instigator_type=InstigatorType.SENSOR
            )
            assert len(sensor_states) == 3

            # No new tick yet for A since only 15 seconds have passed
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=1,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "auto_materialize_sensor_b", expected_num_ticks=1)

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=2,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "auto_materialize_sensor_b", expected_num_ticks=2)

            # Starting a default sensor causes it to make ticks too
            result = result.start_sensor("default_automation_condition_sensor")
            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            sensor_states = instance.schedule_storage.all_instigator_state(
                instigator_type=InstigatorType.SENSOR
            )

            assert len(sensor_states) == 3
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=2,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "auto_materialize_sensor_b", expected_num_ticks=3)
            _assert_sensor_state(
                instance, "default_automation_condition_sensor", expected_num_ticks=1
            )

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=3,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "auto_materialize_sensor_b", expected_num_ticks=4)
            _assert_sensor_state(
                instance, "default_automation_condition_sensor", expected_num_ticks=1
            )

            result = result.with_current_time_advanced(seconds=15)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=3,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(instance, "auto_materialize_sensor_b", expected_num_ticks=5)
            _assert_sensor_state(
                instance, "default_automation_condition_sensor", expected_num_ticks=2
            )

            # Stop each sensor, ticks stop too
            result = result.stop_sensor("auto_materialize_sensor_b")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.DECLARED_IN_CODE,
            )
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance, "default_automation_condition_sensor", expected_num_ticks=3
            )

            result = result.stop_sensor("auto_materialize_sensor_a")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance, "default_automation_condition_sensor", expected_num_ticks=4
            )

            result = result.stop_sensor("default_automation_condition_sensor")
            result = result.with_current_time_advanced(seconds=30)
            result = result.evaluate_tick()

            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_a",
                expected_num_ticks=4,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "auto_materialize_sensor_b",
                expected_num_ticks=5,
                expected_status=InstigatorStatus.STOPPED,
            )
            _assert_sensor_state(
                instance,
                "default_automation_condition_sensor",
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
    with get_daemon_instance(
        extra_overrides={"auto_materialize": {"use_sensors": False}}
    ) as instance:
        scenario_time = daemon_scenario.initial_spec.current_time
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
        extra_overrides={
            "retention": {
                "auto_materialize": {"purge_after_days": {"skipped": 2}},
            },
            "auto_materialize": {"use_sensors": False},
        },
    ) as instance:
        freeze_datetime = get_current_datetime()

        _create_tick(
            instance, TickStatus.SKIPPED, (freeze_datetime - datetime.timedelta(days=8)).timestamp()
        )
        _create_tick(
            instance, TickStatus.SKIPPED, (freeze_datetime - datetime.timedelta(days=6)).timestamp()
        )
        tick_1 = _create_tick(
            instance, TickStatus.SKIPPED, (freeze_datetime - datetime.timedelta(days=1)).timestamp()
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
