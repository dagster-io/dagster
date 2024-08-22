from datetime import datetime, timedelta

from dagster._core.definitions.events import AssetMaterialization
from dagster._core.test_utils import freeze_time

from .conftest import (
    assert_expected_key_order,
    build_and_invoke_sensor,
    build_dag_assets,
    make_test_instance,
)


def test_dag_and_task_metadata() -> None:
    """Test the metadata produced by a sensor for a single dag and task."""
    freeze_datetime = datetime(2021, 1, 1)

    instance = make_test_instance()
    with freeze_time(freeze_datetime):
        result = build_and_invoke_sensor(
            instance=instance,
            defs=build_dag_assets(tasks_to_asset_deps_graph={"1": {"a": []}}),  # dag will have id 2
        )
        assert len(result.asset_events) == 2
        assert_expected_key_order(result.asset_events, ["a", "2"])  # type: ignore
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
        }
        assert set(task_mat.metadata.keys()) == expected_task_metadata_keys

        assert task_mat.metadata["Airflow Run ID"].value == "run"
        assert (
            task_mat.metadata["Start Date"].value
            == (freeze_datetime + timedelta(days=1)).timestamp()
        )
        assert (
            task_mat.metadata["End Date"].value == (freeze_datetime + timedelta(days=2)).timestamp()
        )
        assert task_mat.metadata["Creation Timestamp"].value == freeze_datetime.timestamp()
        assert (
            task_mat.metadata["Run Details"].value
            == "[View Run](http://localhost:8080/dags/2/grid?dag_run_id=run&task_id=1)"
        )
        assert (
            task_mat.metadata["Task Logs"].value
            == "[View Logs](http://localhost:8080/dags/2/grid?dag_run_id=run&task_id=1&tab=logs)"
        )
        assert task_mat.metadata["Airflow Config"].value == {}
        assert task_mat.metadata["Run Type"].value == "manual"

        assert dag_mat.metadata["Airflow Run ID"].value == "run"
        assert dag_mat.metadata["Start Date"].value == freeze_datetime.timestamp()
        assert (
            dag_mat.metadata["End Date"].value == (freeze_datetime + timedelta(days=3)).timestamp()
        )
        assert dag_mat.metadata["Creation Timestamp"].value == freeze_datetime.timestamp()
        assert (
            dag_mat.metadata["Run Details"].value
            == "[View Run](http://localhost:8080/dags/2/grid?dag_run_id=run&tab=details)"
        )
        assert dag_mat.metadata["Airflow Config"].value == {}
        assert dag_mat.metadata["Run Type"].value == "manual"


def test_interleaved_exeutions() -> None:
    """Test that the when task / dag completion is interleaved, the correct ordering is preserved."""
    # Asset graph structure:
    #   a -> b where a and b are each in their own airflow tasks.
    #   c -> d where c and d are each in their own airflow tasks, in a different dag.
    freeze_datetime = datetime(2021, 1, 1)

    instance = make_test_instance()
    with freeze_time(freeze_datetime):
        result = build_and_invoke_sensor(
            instance=instance,
            defs=[
                *build_dag_assets(
                    tasks_to_asset_deps_graph={"1": {"a": []}, "2": {"b": ["a"]}}, dag_id="5"
                ),
                *build_dag_assets(
                    tasks_to_asset_deps_graph={"3": {"c": []}, "4": {"d": ["c"]}}, dag_id="6"
                ),
            ],
        )
        # We expect one asset materialization per asset.
        assert len(result.asset_events) == 6
        assert all(isinstance(event, AssetMaterialization) for event in result.asset_events)
        assert_expected_key_order(result.asset_events, ["a", "b", "c", "d", "5", "6"])  # type: ignore
