from datetime import datetime
from typing import List

from dagster import AssetSpec, SensorResult, asset, build_sensor_context, multi_asset, repository
from dagster_airlift.core.airflow_instance import DagRun, TaskInstance
from dagster_airlift.core.sensor import build_airflow_polling_sensor

from .conftest import DummyInstance


def test_complex_dependencies() -> None:
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
    dag_start = datetime(2021, 1, 1).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    t1_end = datetime(2021, 1, 2).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    t2_end = datetime(2021, 1, 3).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    dag_end = datetime(2021, 1, 4).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    class ComplexDependencyInstance(DummyInstance):
        def get_dag_runs(
            self, dag_id: str, start_date: datetime, end_date: datetime
        ) -> List[DagRun]:
            return [
                DagRun(
                    metadata={
                        "run_type": "manual",
                        "conf": {},
                        "start_date": dag_start,
                        "end_date": dag_end,
                        "state": "success",
                    },
                    dag_id="foo",
                    run_id="run",
                    webserver_url="http://localhost:8080",
                )
            ]

        def get_task_instance(self, dag_id: str, task_id: str, run_id: str) -> TaskInstance:
            if task_id == "1":
                return TaskInstance(
                    metadata={
                        "note": "note",
                        "start_date": dag_start,
                        "end_date": t1_end,
                        "state": "success",
                    },
                    dag_id="some_dag",
                    task_id=task_id,
                    webserver_url="http://localhost:8080",
                    run_id=run_id,
                )
            else:
                return TaskInstance(
                    metadata={
                        "note": "note",
                        "start_date": t1_end,
                        "end_date": t2_end,
                        "state": "success",
                    },
                    dag_id="some_dag",
                    task_id=task_id,
                    webserver_url="http://localhost:8080",
                    run_id=run_id,
                )

    @multi_asset(
        specs=[
            AssetSpec(key="a"),
            AssetSpec(key="b", deps=["a"]),
            AssetSpec(key="c", deps=["a"]),
            AssetSpec(key="d", deps=["b", "c"]),
        ],
    )
    def foo__1():
        pass

    @multi_asset(
        specs=[
            AssetSpec(key="e", deps=["d"]),
            AssetSpec(key="f", deps=["d"]),
        ],
    )
    def foo__2():
        pass

    @asset(op_tags={"airlift/dag_id": "foo"})
    def foo():
        pass

    @repository
    def repo_def():
        return [foo__1, foo__2, foo]

    context = build_sensor_context(repository_def=repo_def)
    sensor_def = build_airflow_polling_sensor(
        airflow_instance=ComplexDependencyInstance(),
    )
    result = sensor_def(context)
    assert isinstance(result, SensorResult)
    assert [asset_event.asset_key.to_user_string() for asset_event in result.asset_events] == [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "foo",
    ]
