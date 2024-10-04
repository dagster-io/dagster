from datetime import datetime, timedelta, timezone
from typing import Sequence

import mock
import pytest
from dagster import (
    AssetCheckKey,
    AssetKey,
    AssetSpec,
    DagsterInstance,
    Definitions,
    SensorResult,
    _check as check,
    asset,
    asset_check,
    build_sensor_context,
)
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TimestampMetadataValue
from dagster._core.definitions.sensor_definition import SensorEvaluationContext
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.test_utils import freeze_time
from dagster._serdes import deserialize_value
from dagster._time import get_current_datetime
from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    EFFECTIVE_TIMESTAMP_METADATA_KEY,
    TASK_ID_TAG_KEY,
)
from dagster_airlift.core import dag_defs, task_defs
from dagster_airlift.core.airflow_defs_data import AirflowDefinitionsData
from dagster_airlift.core.load_defs import build_full_automapped_dags_from_airflow_instance
from dagster_airlift.core.sensor.sensor_builder import (
    AirflowPollingSensorCursor,
    AirliftSensorEventTransformerError,
)
from dagster_airlift.core.serialization.defs_construction import (
    key_for_automapped_task_asset,
    make_default_dag_asset_key,
)
from dagster_airlift.test import make_dag_run, make_instance

from dagster_airlift_tests.unit_tests.conftest import (
    assert_expected_key_order,
    build_and_invoke_sensor,
    fully_loaded_repo_from_airflow_asset_graph,
)


def make_dag_key(dag_id: str) -> AssetKey:
    return AssetKey(["test_instance", "dag", dag_id])


def make_dag_key_str(dag_id: str) -> str:
    return make_dag_key(dag_id).to_user_string()


def test_dag_and_task_metadata(init_load_context: None, instance: DagsterInstance) -> None:
    """Test the metadata produced by a sensor for a single dag and task."""
    freeze_datetime = datetime(2021, 1, 1)

    with freeze_time(freeze_datetime):
        result, _ = build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            instance=instance,
        )
        assert len(result.asset_events) == 2
        assert_expected_key_order(result.asset_events, ["a", make_dag_key_str("dag")])
        dag_mat = result.asset_events[1]
        expected_dag_metadata_keys = {
            "Airflow Run ID",
            "Start Date",
            "End Date",
            "Run Metadata (raw)",
            "Creation Timestamp",
            "Run Details",
            "Airflow Config",
            "Run Type",
            "dagster-airlift/effective_timestamp",
        }
        assert set(dag_mat.metadata.keys()) == expected_dag_metadata_keys
        task_mat = result.asset_events[0]
        expected_task_metadata_keys = {
            "Airflow Run ID",
            "Start Date",
            "End Date",
            "Run Metadata (raw)",
            "Creation Timestamp",
            "Run Details",
            "Task Logs",
            "Airflow Config",
            "Run Type",
            "dagster-airlift/effective_timestamp",
        }
        assert set(task_mat.metadata.keys()) == expected_task_metadata_keys

        assert task_mat.metadata["Airflow Run ID"].value == "run-dag"
        assert (
            task_mat.metadata["Start Date"].value
            == (freeze_datetime - timedelta(minutes=10)).timestamp()
        )
        assert (
            task_mat.metadata["End Date"].value
            == (freeze_datetime - timedelta(seconds=1)).timestamp()
        )
        assert task_mat.metadata["Creation Timestamp"].value == freeze_datetime.timestamp()
        assert (
            task_mat.metadata["Run Details"].value
            == "[View Run](http://dummy.domain/dags/dag/grid?dag_run_id=run-dag&task_id=task)"
        )
        assert (
            task_mat.metadata["Task Logs"].value
            == "[View Logs](http://dummy.domain/dags/dag/grid?dag_run_id=run-dag&task_id=task&tab=logs)"
        )
        assert task_mat.metadata["Airflow Config"].value == {}
        assert task_mat.metadata["Run Type"].value == "manual"

        assert dag_mat.metadata["Airflow Run ID"].value == "run-dag"
        assert (
            dag_mat.metadata["Start Date"].value
            == (freeze_datetime - timedelta(minutes=10)).timestamp()
        )
        assert dag_mat.metadata["End Date"].value == freeze_datetime.timestamp()
        assert dag_mat.metadata["Creation Timestamp"].value == freeze_datetime.timestamp()
        assert (
            dag_mat.metadata["Run Details"].value
            == "[View Run](http://dummy.domain/dags/dag/grid?dag_run_id=run-dag&tab=details)"
        )
        assert dag_mat.metadata["Airflow Config"].value == {}
        assert dag_mat.metadata["Run Type"].value == "manual"


def test_interleaved_executions(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that the when task / dag completion is interleaved the correct ordering is preserved."""
    # Asset graph structure:
    #   a -> b where a and b are each in their own airflow tasks.
    #   c -> d where c and d are each in their own airflow tasks, in a different dag.
    freeze_datetime = datetime(2021, 1, 1)
    with freeze_time(freeze_datetime):
        result, context = build_and_invoke_sensor(
            assets_per_task={
                "dag1": {"task1": [("a", [])], "task2": [("b", ["a"])]},
                "dag2": {"task1": [("c", [])], "task2": [("d", ["c"])]},
            },
            instance=instance,
        )
        # We expect one asset materialization per asset.
        assert len(result.asset_events) == 6
        assert all(isinstance(event, AssetMaterialization) for event in result.asset_events)

        mats_order = [mat.asset_key.to_user_string() for mat in result.asset_events]
        # a should be before b
        assert mats_order.index("a") < mats_order.index("b")
        # c should be before d
        assert mats_order.index("c") < mats_order.index("d")
        # dag1 and dag2 should be after all task-mapped assets
        assert mats_order.index(make_dag_key_str("dag1")) >= 4
        assert mats_order.index(make_dag_key_str("dag2")) >= 4
        assert context.cursor
        cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert cursor.end_date_gte == freeze_datetime.timestamp()
        assert cursor.end_date_lte is None
        assert cursor.dag_query_offset == 0


def test_dependencies_within_tasks(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that a complex asset graph structure can be ingested in correct order from the sensor.
    Where a, b, and c are part of task 1, and d, e, and f are part of task 2.
    """
    # Asset graph structure:
    #   a
    #  / \
    # b   c
    #  \ /
    #   d
    #  / \
    # e   f
    freeze_datetime = datetime(2021, 1, 1)
    with freeze_time(freeze_datetime):
        result, context = build_and_invoke_sensor(
            assets_per_task={
                "dag": {
                    "task1": [("a", []), ("b", ["a"]), ("c", ["a"])],
                    "task2": [("d", ["b", "c"]), ("e", ["d"]), ("f", ["d"])],
                },
            },
            instance=instance,
        )
        assert len(result.asset_events) == 7
        assert_expected_key_order(
            result.asset_events, ["a", "b", "c", "d", "e", "f", make_dag_key_str("dag")]
        )
        assert context.cursor
        cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert cursor.end_date_gte == freeze_datetime.timestamp()
        assert cursor.end_date_lte is None
        assert cursor.dag_query_offset == 0


def test_outside_of_dag_dependency(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that if an asset has a transitive dependency on another asset within the same task, ordering is respected."""
    # a -> b -> c where a and c are in the same task, and b is not in any dag.
    freeze_datetime = datetime(2021, 1, 1)
    with freeze_time(freeze_datetime):
        result, context = build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", []), ("c", ["b"])]},
            },
            additional_defs=Definitions(assets=[AssetSpec(key="b", deps=["a"])]),
            instance=instance,
        )
        assert len(result.asset_events) == 3
        assert all(isinstance(event, AssetMaterialization) for event in result.asset_events)
        assert_expected_key_order(result.asset_events, ["a", "c", make_dag_key_str("dag")])
        assert context.cursor
        cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert cursor.end_date_gte == freeze_datetime.timestamp()
        assert cursor.end_date_lte is None
        assert cursor.dag_query_offset == 0


def test_request_asset_checks(init_load_context: None, instance: DagsterInstance) -> None:
    """Test that when a new dag or task run is detected, a new check run is requested for all checks which may target that dag/task."""
    freeze_datetime = datetime(2021, 1, 1)

    dag_asset_key = make_dag_key("dag")

    @asset_check(asset="a")
    def check_task_asset():
        pass

    @asset_check(asset=dag_asset_key)
    def check_dag_asset():
        pass

    @asset_check(asset="c")
    def check_unrelated_asset():
        pass

    with freeze_time(freeze_datetime):
        result, context = build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", []), ("b", ["a"])]},
            },
            additional_defs=Definitions(
                asset_checks=[check_task_asset, check_dag_asset, check_unrelated_asset],
                assets=[AssetSpec(key="c")],
            ),
            instance=instance,
        )

        assert len(result.asset_events) == 3
        assert result.run_requests
        assert len(result.run_requests) == 1
        run_request = result.run_requests[0]
        assert run_request.asset_check_keys
        assert set(run_request.asset_check_keys) == {
            AssetCheckKey(name="check_task_asset", asset_key=AssetKey(["a"])),
            AssetCheckKey(name="check_dag_asset", asset_key=dag_asset_key),
        }
        assert context.cursor
        cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert cursor.end_date_gte == freeze_datetime.timestamp()
        assert cursor.end_date_lte is None
        assert cursor.dag_query_offset == 0


_CALLCOUNT = [0]


def _mock_get_current_datetime() -> datetime:
    if _CALLCOUNT[0] < 2:
        _CALLCOUNT[0] += 1
        return datetime(2021, 2, 1, tzinfo=timezone.utc)
    next_time = datetime(2021, 2, 1, tzinfo=timezone.utc) + timedelta(seconds=46 * _CALLCOUNT[0])
    _CALLCOUNT[0] += 1
    return next_time


def test_cursor(init_load_context: None, instance: DagsterInstance) -> None:
    """Test expected cursor behavior for sensor."""
    asset_and_dag_structure = {
        "dag1": {"task1": [("a", [])]},
        "dag2": {"task1": [("b", [])]},
    }

    with freeze_time(datetime(2021, 1, 1, tzinfo=timezone.utc)):
        # First, run through a full successful iteration of the sensor. Expect time to move forward, and polled dag id to be None, since we completed iteration of all dags.
        # Then, run through a partial iteration of the sensor. We mock get_current_datetime to return a time after timeout passes iteration start after the first call, meaning we should pause iteration.
        repo_def = fully_loaded_repo_from_airflow_asset_graph(asset_and_dag_structure)
        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)
        assert context.cursor
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert new_cursor.end_date_gte == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.end_date_lte is None
        assert new_cursor.dag_query_offset == 0

    with mock.patch(
        "dagster._time._mockable_get_current_datetime", wraps=_mock_get_current_datetime
    ):
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        # We didn't advance to the next effective timestamp, since we didn't complete iteration
        assert new_cursor.end_date_gte == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        # We have not yet moved forward
        assert new_cursor.end_date_lte == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.dag_query_offset == 1

        _CALLCOUNT[0] = 0
        # We weren't able to complete iteration, so we should pause iteration again
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert new_cursor.end_date_gte == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.end_date_lte == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.dag_query_offset == 2

        _CALLCOUNT[0] = 0
        # Now it should finish iteration.
        result = sensor(context)
        assert isinstance(result, SensorResult)
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert new_cursor.end_date_gte == datetime(2021, 2, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.end_date_lte is None
        assert new_cursor.dag_query_offset == 0


def test_legacy_cursor(init_load_context: None, instance: DagsterInstance) -> None:
    """Test the case where a legacy/uninterpretable cursor is provided to the sensor execution."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)
    with freeze_time(freeze_datetime):
        repo_def = fully_loaded_repo_from_airflow_asset_graph({"dag": {"task": [("a", [])]}})
        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(
            repository_def=repo_def, cursor=str(freeze_datetime.timestamp()), instance=instance
        )
        result = sensor(context)
        assert isinstance(result, SensorResult)
        assert context.cursor
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert new_cursor.end_date_gte == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.end_date_lte is None
        assert new_cursor.dag_query_offset == 0


def test_no_runs(init_load_context: None, instance: DagsterInstance) -> None:
    """Test the case with no runs."""
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)
    with freeze_time(freeze_datetime):
        repo_def = fully_loaded_repo_from_airflow_asset_graph(
            {"dag": {"task": [("a", [])]}},
            create_runs=False,
        )
        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)
        assert context.cursor
        new_cursor = deserialize_value(context.cursor, AirflowPollingSensorCursor)
        assert new_cursor.end_date_gte == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
        assert new_cursor.end_date_lte is None
        assert new_cursor.dag_query_offset == 0
        assert not result.asset_events
        assert not result.run_requests


def test_automapped_tasks_only(init_load_context: None, instance: DagsterInstance) -> None:
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)
    with freeze_time(freeze_datetime):
        dag_id = "dag1"
        dag_runs = [
            make_dag_run(
                dag_id=dag_id,
                run_id=f"run-{dag_id}",
                start_date=get_current_datetime() - timedelta(minutes=10),
                end_date=get_current_datetime(),
            )
        ]

        airflow_instance = make_instance(
            dag_and_task_structure={dag_id: ["task1", "task2"]},
            task_deps={"task1": [], "task2": ["task1"]},
            dag_runs=dag_runs,
            instance_name="test_instance",
        )

        automapped_defs = build_full_automapped_dags_from_airflow_instance(
            airflow_instance=airflow_instance,
        )

        repo_def = automapped_defs.get_repository_def()

        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)

        asset_mats = check.is_list(result.asset_events, of_type=AssetMaterialization)

        asset_mat_dict = {mat.asset_key: mat for mat in asset_mats}

        am_task1_key = key_for_automapped_task_asset("test_instance", dag_id, "task1")
        am_task2_key = key_for_automapped_task_asset("test_instance", dag_id, "task2")
        dag1_asset_key = make_default_dag_asset_key("test_instance", dag_id)

        assert am_task1_key in asset_mat_dict
        assert am_task2_key in asset_mat_dict
        assert dag1_asset_key in asset_mat_dict


def test_automapped_tasks_with_explicit_external_asset_defs(
    init_load_context: None, instance: DagsterInstance
) -> None:
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)
    with freeze_time(freeze_datetime):
        dag_id = "dag1"
        dag_runs = [
            make_dag_run(
                dag_id=dag_id,
                run_id=f"run-{dag_id}",
                start_date=get_current_datetime() - timedelta(minutes=10),
                end_date=get_current_datetime(),
            )
        ]

        airflow_instance = make_instance(
            dag_and_task_structure={dag_id: ["task1", "task2"]},
            task_deps={"task1": [], "task2": ["task1"]},
            dag_runs=dag_runs,
            instance_name="test_instance",
        )

        explicit_asset1 = AssetSpec(key="explicit_asset1")
        explicit_asset2 = AssetSpec(key="explicit_asset2")

        automapped_defs = build_full_automapped_dags_from_airflow_instance(
            airflow_instance=airflow_instance,
            defs=dag_defs(
                "dag1",
                task_defs("task1", Definitions(assets=[explicit_asset1])),
                task_defs("task2", Definitions(assets=[explicit_asset2])),
            ),
        )

        am_task1_key = key_for_automapped_task_asset("test_instance", dag_id, "task1")
        am_task2_key = key_for_automapped_task_asset("test_instance", dag_id, "task2")
        dag1_asset_key = make_default_dag_asset_key("test_instance", dag_id)

        spec_dict = {spec.key: spec for spec in automapped_defs.get_all_asset_specs()}

        assert set(spec_dict.keys()) == {
            am_task1_key,
            am_task2_key,
            dag1_asset_key,
            explicit_asset1.key,
            explicit_asset2.key,
        }

        repo_def = automapped_defs.get_repository_def()

        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)

        # there should be 5 asset materializations. 1 for dag, 2 for tasks, and 2 for explicit assets

        asset_mats = check.is_list(result.asset_events, of_type=AssetMaterialization)

        asset_mat_dict = {mat.asset_key: mat for mat in asset_mats}

        assert set(asset_mat_dict.keys()) == {
            am_task1_key,
            am_task2_key,
            dag1_asset_key,
            explicit_asset1.key,
            explicit_asset2.key,
        }


def test_automapped_tasks_with_explicit_materializable_asset_defs(
    init_load_context: None, instance: DagsterInstance
) -> None:
    freeze_datetime = datetime(2021, 1, 1, tzinfo=timezone.utc)
    with freeze_time(freeze_datetime):
        dag_id = "dag1"
        dag_run_id = f"run-{dag_id}"
        dag_runs = [
            make_dag_run(
                dag_id=dag_id,
                run_id=f"run-{dag_id}",
                start_date=get_current_datetime() - timedelta(minutes=10),
                end_date=get_current_datetime(),
            )
        ]

        airflow_instance = make_instance(
            dag_and_task_structure={dag_id: ["task1", "task2"]},
            task_deps={"task1": [], "task2": ["task1"]},
            dag_runs=dag_runs,
            instance_name="test_instance",
        )

        @asset
        def explicit_asset1() -> None:
            pass

        @asset
        def explicit_asset2() -> None:
            pass

        automapped_defs = build_full_automapped_dags_from_airflow_instance(
            airflow_instance=airflow_instance,
            defs=dag_defs(
                "dag1",
                task_defs("task1", Definitions(assets=[explicit_asset1])),
                task_defs("task2", Definitions(assets=[explicit_asset2])),
            ),
        )

        am_task1_key = key_for_automapped_task_asset("test_instance", dag_id, "task1")
        am_task2_key = key_for_automapped_task_asset("test_instance", dag_id, "task2")
        dag1_asset_key = make_default_dag_asset_key("test_instance", dag_id)

        spec_dict = {spec.key: spec for spec in automapped_defs.get_all_asset_specs()}

        assert set(spec_dict.keys()) == {
            am_task1_key,
            am_task2_key,
            dag1_asset_key,
            explicit_asset1.key,
            explicit_asset2.key,
        }

        repo_def = automapped_defs.get_repository_def()

        # we simulate runs from the proxy operator for both tasks
        assert simulate_materialize_from_proxy_operator(
            instance=instance,
            assets_def=explicit_asset1,
            dag_id=dag_id,
            task_id="task1",
            dag_run_id=dag_run_id,
        ).success
        assert simulate_materialize_from_proxy_operator(
            instance=instance,
            assets_def=explicit_asset1,
            dag_id=dag_id,
            task_id="task2",
            dag_run_id=dag_run_id,
        ).success

        sensor = next(iter(repo_def.sensor_defs))
        context = build_sensor_context(repository_def=repo_def, instance=instance)
        result = sensor(context)
        assert isinstance(result, SensorResult)

        # there should be 3 asset materializations. 1 for dag, 2 for automapped tasks

        asset_mats = check.is_list(result.asset_events, of_type=AssetMaterialization)

        asset_mat_dict = {mat.asset_key: mat for mat in asset_mats}

        assert set(asset_mat_dict.keys()) == {
            am_task1_key,
            am_task2_key,
            dag1_asset_key,
            # explicit_asset1.key, # no syntheic materialization for explicit asset as it was proxied
            # explicit_asset2.key, # no syntheic materialization for explicit asset as it waws proxied
        }


def simulate_materialize_from_proxy_operator(
    *,
    instance: DagsterInstance,
    assets_def: AssetsDefinition,
    dag_run_id: str,
    dag_id: str,
    task_id: str,
) -> ExecuteInProcessResult:
    # TODO consolidate with code in proxy operator
    tags = {
        DAG_ID_TAG_KEY: dag_id,
        DAG_RUN_ID_TAG_KEY: dag_run_id,
        TASK_ID_TAG_KEY: task_id,
    }
    return materialize(assets=[assets_def], instance=instance, tags=tags)


def test_pluggable_transformation(init_load_context: None, instance: DagsterInstance) -> None:
    """Test the case where a custom transformation is provided to the sensor."""

    def pluggable_event_transformer(
        context: SensorEvaluationContext,
        airflow_data: AirflowDefinitionsData,
        events: Sequence[AssetMaterialization],
    ) -> Sequence[AssetMaterialization]:
        assert isinstance(context, SensorEvaluationContext)
        assert isinstance(airflow_data, AirflowDefinitionsData)
        # Change the timestamp, which should also change the order. We expect this to be respected by the sensor.
        new_events = []
        for event in events:
            if AssetKey(["a"]) == event.asset_key:
                new_events.append(
                    event._replace(
                        metadata={
                            "test": "test",
                            EFFECTIVE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(1.0),
                        }
                    )
                )
            elif AssetKey.from_user_string(make_dag_key_str("dag")) == event.asset_key:
                new_events.append(
                    event._replace(
                        metadata={
                            "test": "test",
                            EFFECTIVE_TIMESTAMP_METADATA_KEY: TimestampMetadataValue(0.0),
                        }
                    )
                )
        return new_events

    result, context = build_and_invoke_sensor(
        assets_per_task={
            "dag": {"task": [("a", [])]},
        },
        instance=instance,
        event_transformer_fn=pluggable_event_transformer,
    )
    assert len(result.asset_events) == 2
    assert_expected_key_order(result.asset_events, [make_dag_key_str("dag"), "a"])
    for event in result.asset_events:
        assert set(event.metadata.keys()) == {"test", EFFECTIVE_TIMESTAMP_METADATA_KEY}


def test_user_code_error_pluggable_transformation(
    init_load_context: None, instance: DagsterInstance
) -> None:
    """Test the case where a custom transformation is provided to the sensor, and the user code raises an error."""

    def pluggable_event_transformer(
        context: SensorEvaluationContext,
        airflow_data: AirflowDefinitionsData,
        events: Sequence[AssetMaterialization],
    ) -> Sequence[AssetMaterialization]:
        raise ValueError("User code error")

    with pytest.raises(AirliftSensorEventTransformerError):
        build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            instance=instance,
            event_transformer_fn=pluggable_event_transformer,
        )


def test_missing_effective_timestamp_pluggable_impl(
    init_load_context: None, instance: DagsterInstance
) -> None:
    """Test the case where a custom transformation is provided to the sensor, and the user doesn't include effective timestamp metadata."""

    def missing_effective_timestamp(
        context: SensorEvaluationContext,
        airflow_data: AirflowDefinitionsData,
        events: Sequence[AssetMaterialization],
    ) -> Sequence[AssetMaterialization]:
        return [event._replace(metadata={}) for event in events]

    with pytest.raises(DagsterInvariantViolationError):
        build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            instance=instance,
            event_transformer_fn=missing_effective_timestamp,
        )


def test_nonsense_result_pluggable_impl(init_load_context: None, instance: DagsterInstance) -> None:
    """Test the case where a nonsense result is returned from the custom transformation."""

    def nonsense_result(
        context: SensorEvaluationContext,
        airflow_data: AirflowDefinitionsData,
        events: Sequence[AssetMaterialization],
    ) -> Sequence[AssetMaterialization]:
        return [1, 2, 3]  # type: ignore # intentionally wrong

    with pytest.raises(DagsterInvariantViolationError):
        build_and_invoke_sensor(
            assets_per_task={
                "dag": {"task": [("a", [])]},
            },
            instance=instance,
            event_transformer_fn=nonsense_result,
        )
