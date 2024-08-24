from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

import requests
from dagster import (
    AssetsDefinition,
    AssetSpec,
    SensorResult,
    asset,
    build_sensor_context,
    multi_asset,
    repository,
)
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._time import get_current_datetime
from dagster_airlift.core import AirflowInstance
from dagster_airlift.core.airflow_instance import DagRun, TaskInfo, TaskInstance
from dagster_airlift.core.basic_auth import AirflowAuthBackend
from dagster_airlift.core.sensor import build_airflow_polling_sensor


def strip_to_first_of_month(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class DummyAuthBackend(AirflowAuthBackend):
    def get_session(self) -> requests.Session:
        raise NotImplementedError("This shouldn't be called from this mock context.")

    def get_webserver_url(self) -> str:
        return "http://dummy.domain"


class DummyInstance(AirflowInstance):
    """A dummy instance that returns a single dag run and task instance for each call.
    Designed in such a way that timestamps mirror the task_id, so that we can easily test ordering.
    If you want some task to complete after a different task, you can simply set the task_id to a higher number.
    The dag id should be a number higher than any task id it contains, so that it will complete after all constituent tasks.
    This instance is designed to be used with "frozen" time, so that a baseline can be established for testing.
    """

    def __init__(self) -> None:
        super().__init__(
            auth_backend=DummyAuthBackend(),
            name="dummy_instance",
        )

    def get_dag_runs(self, dag_id: str, start_date: datetime, end_date: datetime) -> List[DagRun]:
        """Return a single dag run that started and finished within the given range."""
        cur_date = strip_to_first_of_month(get_current_datetime())
        return [
            make_dag_run(cur_date, cur_date + timedelta(days=int(dag_id) + 1), dag_id),
        ]

    def get_task_instance(self, dag_id: str, task_id: str, run_id: str) -> TaskInstance:
        """Return a task instance that started and finished within the given range. Expects that time has been frozen."""
        cur_date = strip_to_first_of_month(get_current_datetime())
        return make_task_instance(
            dag_id,
            task_id,
            cur_date + timedelta(days=int(task_id)),
            cur_date + timedelta(days=int(task_id) + 1),
        )

    def get_task_info(self, dag_id, task_id) -> TaskInfo:
        return TaskInfo(
            webserver_url="http://localhost:8080", dag_id=dag_id, task_id=task_id, metadata={}
        )

    def get_dag_source_code(self, file_token: str) -> str:
        return "source code"


def make_dag_run(dag_start: datetime, dag_end: datetime, dag_id: str) -> DagRun:
    return DagRun(
        metadata={
            "run_type": "manual",
            "conf": {},
            "start_date": dag_start.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "end_date": dag_end.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "state": "success",
        },
        dag_id=dag_id,
        run_id="run",
        webserver_url="http://localhost:8080",
    )


def make_task_instance(
    dag_id: str, task_id: str, task_start: datetime, task_end: datetime
) -> TaskInstance:
    return TaskInstance(
        metadata={
            "note": "note",
            "start_date": task_start.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "end_date": task_end.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "state": "success",
        },
        dag_id=dag_id,
        task_id=task_id,
        webserver_url="http://localhost:8080",
        run_id="run",
    )


def build_task_asset(
    deps_graph: Dict[str, List[str]],
    task_id: str,
    dag_id: str,
) -> AssetsDefinition:
    asset_specs = [AssetSpec(key=key, deps=deps) for key, deps in deps_graph.items()]

    @multi_asset(specs=asset_specs, op_tags={"airlift/task_id": task_id, "airlift/dag_id": dag_id})
    def asset_fn():
        pass

    return asset_fn


def build_dag_asset(
    dag_id: str,
) -> AssetsDefinition:
    @asset(op_tags={"airlift/dag_id": dag_id}, key=dag_id)
    def asset_fn():
        pass

    return asset_fn


def make_test_instance(
    get_task_instance_override=None, get_dag_runs_override=None, list_dags_override=None
) -> DummyInstance:
    klass_to_instantiate = DummyInstance
    if get_task_instance_override:

        class TaskInstanceOverride(klass_to_instantiate):
            def get_task_instance(self, dag_id: str, task_id: str, run_id: str) -> TaskInstance:
                return get_task_instance_override(self, dag_id, task_id, run_id)

        klass_to_instantiate = TaskInstanceOverride

    if get_dag_runs_override:

        class DagRunsOverride(klass_to_instantiate):  # type: ignore
            def get_dag_runs(
                self, dag_id: str, start_date: datetime, end_date: datetime
            ) -> List[DagRun]:
                return get_dag_runs_override(self, dag_id, start_date, end_date)

        klass_to_instantiate = DagRunsOverride

    if list_dags_override:

        class ListDagsOverride(klass_to_instantiate):  # type: ignore
            def list_dags(self):
                return list_dags_override(self)

        klass_to_instantiate = ListDagsOverride

    return klass_to_instantiate()


def repo_from_defs(assets_defs: List[AssetsDefinition]) -> RepositoryDefinition:
    @repository
    def repo():
        return assets_defs

    return repo


def build_and_invoke_sensor(
    instance: AirflowInstance,
    defs: List[AssetsDefinition],
) -> SensorResult:
    sensor = build_airflow_polling_sensor(instance)
    context = build_sensor_context(repository_def=repo_from_defs(defs))
    result = sensor(context)
    assert isinstance(result, SensorResult)
    return result


def build_dag_assets(
    tasks_to_asset_deps_graph: Dict[str, Dict[str, List[str]]],
    dag_id: Optional[str] = None,
) -> List[AssetsDefinition]:
    resolved_dag_id = dag_id or str(
        max(int(task_id) for task_id in tasks_to_asset_deps_graph.keys()) + 1
    )
    assets = []
    for task_id, deps_graph in tasks_to_asset_deps_graph.items():
        assets.append(build_task_asset(deps_graph, task_id, resolved_dag_id))
    assets.append(build_dag_asset(resolved_dag_id))
    return assets


def assert_expected_key_order(
    mats: Sequence[AssetMaterialization], expected_key_order: Sequence[str]
) -> None:
    assert [mat.asset_key.to_user_string() for mat in mats] == expected_key_order


def make_asset(key, deps):
    @asset(key=key, deps=deps)
    def the_asset():
        pass

    return the_asset
