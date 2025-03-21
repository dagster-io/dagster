from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Optional

import requests

from dagster_airlift.core import AirflowInstance
from dagster_airlift.core.airflow_instance import DagInfo, DagRun, TaskInfo, TaskInstance
from dagster_airlift.core.basic_auth import AirflowAuthBackend


class DummyAuthBackend(AirflowAuthBackend):
    def get_session(self) -> requests.Session:
        raise NotImplementedError("This shouldn't be called from this mock context.")

    def get_webserver_url(self) -> str:
        return "http://dummy.domain"


class AirflowInstanceFake(AirflowInstance):
    """Loads a set of provided DagInfo, TaskInfo, and TaskInstance objects for testing."""

    def __init__(
        self,
        dag_infos: list[DagInfo],
        task_infos: list[TaskInfo],
        task_instances: list[TaskInstance],
        dag_runs: list[DagRun],
        variables: list[dict[str, Any]] = [],
        instance_name: Optional[str] = None,
        max_runs_per_batch: Optional[int] = None,
    ) -> None:
        self._dag_infos_by_dag_id = {dag_info.dag_id: dag_info for dag_info in dag_infos}
        self._task_infos_by_dag_and_task_id = {
            (task_info.dag_id, task_info.task_id): task_info for task_info in task_infos
        }
        self._task_instances_by_dag_and_task_id: dict[tuple[str, str], list[TaskInstance]] = (
            defaultdict(list)
        )
        for task_instance in task_instances:
            self._task_instances_by_dag_and_task_id[
                (task_instance.dag_id, task_instance.task_id)
            ].append(task_instance)
        self._dag_runs_by_dag_id: dict[str, list[DagRun]] = defaultdict(list)
        for dag_run in dag_runs:
            self._dag_runs_by_dag_id[dag_run.dag_id].append(dag_run)
        self._dag_infos_by_file_token = {dag_info.file_token: dag_info for dag_info in dag_infos}
        self._variables = variables
        self._max_runs_per_batch = max_runs_per_batch
        super().__init__(
            auth_backend=DummyAuthBackend(),
            name="test_instance" if instance_name is None else instance_name,
        )

    def list_dags(self) -> list[DagInfo]:
        return list(self._dag_infos_by_dag_id.values())

    def list_variables(self) -> list[dict[str, Any]]:
        return self._variables

    def get_dag_runs(self, dag_id: str, start_date: datetime, end_date: datetime) -> list[DagRun]:
        if dag_id not in self._dag_runs_by_dag_id:
            raise ValueError(f"Dag run not found for dag_id {dag_id}")
        return [
            run
            for run in self._dag_runs_by_dag_id[dag_id]
            if start_date.timestamp() <= run.start_date.timestamp() <= end_date.timestamp()
            and start_date.timestamp() <= run.end_date.timestamp() <= end_date.timestamp()
        ]

    def get_dag_runs_batch(
        self,
        dag_ids: Sequence[str],
        end_date_gte: datetime,
        end_date_lte: datetime,
        offset: int = 0,
    ) -> tuple[list[DagRun], int]:
        runs = [
            (run.end_date, run)
            for runs in self._dag_runs_by_dag_id.values()
            for run in runs
            if end_date_gte.timestamp() <= run.end_date.timestamp() <= end_date_lte.timestamp()
            and run.dag_id in dag_ids
        ]
        sorted_by_end_date = [run for _, run in sorted(runs, key=lambda x: x[0])]
        end_idx = (
            offset + self._max_runs_per_batch
            if self._max_runs_per_batch
            else len(sorted_by_end_date)
        )
        return (sorted_by_end_date[offset:end_idx], len(sorted_by_end_date))

    def get_task_instance_batch(
        self, dag_id: str, task_ids: Sequence[str], run_id: str, states: Sequence[str]
    ) -> list[TaskInstance]:
        task_instances = []
        for task_id in set(task_ids):
            if (dag_id, task_id) not in self._task_instances_by_dag_and_task_id:
                continue
            task_instances.extend(
                [
                    task_instance
                    for task_instance in self._task_instances_by_dag_and_task_id[(dag_id, task_id)]
                    if task_instance.run_id == run_id and task_instance.state in states
                ]
            )
        return task_instances

    def get_task_instance(self, dag_id: str, task_id: str, run_id: str) -> TaskInstance:
        if (dag_id, task_id) not in self._task_instances_by_dag_and_task_id:
            raise ValueError(f"Task instance not found for dag_id {dag_id} and task_id {task_id}")
        if not any(
            task_instance.run_id == run_id
            for task_instance in self._task_instances_by_dag_and_task_id[(dag_id, task_id)]
        ):
            raise ValueError(
                f"Task instance not found for dag_id {dag_id}, task_id {task_id}, and run_id {run_id}"
            )
        return next(
            iter(
                task_instance
                for task_instance in self._task_instances_by_dag_and_task_id[(dag_id, task_id)]
                if task_instance.run_id == run_id
            )
        )

    def get_task_info(self, dag_id, task_id) -> TaskInfo:  # pyright: ignore[reportIncompatibleMethodOverride]
        if (dag_id, task_id) not in self._task_infos_by_dag_and_task_id:
            raise ValueError(f"Task info not found for dag_id {dag_id} and task_id {task_id}")
        return self._task_infos_by_dag_and_task_id[(dag_id, task_id)]

    def get_task_infos(self, *, dag_id: str) -> list[TaskInfo]:
        if dag_id not in self._dag_infos_by_dag_id:
            raise ValueError(f"Dag info not found for dag_id {dag_id}")
        task_infos = []
        for dag_id, task_id in self._task_infos_by_dag_and_task_id:
            if dag_id == dag_id:
                task_infos.append(self._task_infos_by_dag_and_task_id[(dag_id, task_id)])
        return task_infos

    def get_dag_info(self, dag_id) -> DagInfo:
        if dag_id not in self._dag_infos_by_dag_id:
            raise ValueError(f"Dag info not found for dag_id {dag_id}")
        return self._dag_infos_by_dag_id[dag_id]

    def get_dag_source_code(self, file_token: str) -> str:
        if file_token not in self._dag_infos_by_file_token:
            raise ValueError(f"Dag info not found for file_token {file_token}")
        return "indicates found source code"


def make_dag_info(dag_id: str, file_token: Optional[str]) -> DagInfo:
    return DagInfo(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        metadata={"file_token": file_token if file_token else "dummy_file_token"},
    )


def make_task_info(
    dag_id: str, task_id: str, downstream_task_ids: Optional[list[str]] = None
) -> TaskInfo:
    return TaskInfo(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        task_id=task_id,
        metadata={"downstream_task_ids": downstream_task_ids or []},
    )


def make_task_instance(
    dag_id: str,
    task_id: str,
    run_id: str,
    start_date: datetime,
    end_date: datetime,
    logical_date: Optional[datetime] = None,
) -> TaskInstance:
    return TaskInstance(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        task_id=task_id,
        run_id=run_id,
        metadata={
            "state": "success",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "logical_date": logical_date.isoformat() if logical_date else start_date.isoformat(),
        },
    )


def make_dag_run(
    dag_id: str,
    run_id: str,
    start_date: datetime,
    end_date: datetime,
    logical_date: Optional[datetime] = None,
) -> DagRun:
    return DagRun(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        run_id=run_id,
        metadata={
            "state": "success",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "logical_date": logical_date.isoformat() if logical_date else start_date.isoformat(),
            "run_type": "manual",
            "note": "dummy note",
            "conf": {},
        },
    )


def make_instance(
    dag_and_task_structure: dict[str, list[str]],
    dag_runs: list[DagRun] = [],
    task_deps: dict[str, list[str]] = {},
    instance_name: Optional[str] = None,
    max_runs_per_batch: Optional[int] = None,
) -> AirflowInstanceFake:
    """Constructs DagInfo, TaskInfo, and TaskInstance objects from provided data.

    Args:
        dag_and_task_structure: A dictionary mapping dag_id to a list of task_ids.
        dag_runs: A list of DagRun objects to include in the instance. A TaskInstance object will be
            created for each task_id in the dag, for each DagRun in dag_runs pertaining to a particular dag.
    """
    dag_infos = []
    task_infos = []
    for dag_id, task_ids in dag_and_task_structure.items():
        dag_info = make_dag_info(dag_id=dag_id, file_token=dag_id)
        dag_infos.append(dag_info)
        task_infos.extend(
            [
                make_task_info(
                    dag_id=dag_id, task_id=task_id, downstream_task_ids=task_deps.get(task_id, [])
                )
                for task_id in task_ids
            ]
        )
    task_instances = []
    for dag_run in dag_runs:
        task_instances.extend(
            [
                make_task_instance(
                    dag_id=dag_run.dag_id,
                    task_id=task_id,
                    run_id=dag_run.run_id,
                    start_date=dag_run.start_date,
                    end_date=dag_run.end_date
                    - timedelta(
                        seconds=1
                    ),  # Ensure that the task ends before the full "dag" completes.
                    logical_date=dag_run.logical_date,
                )
                for task_id in dag_and_task_structure[dag_run.dag_id]
            ]
        )
    return AirflowInstanceFake(
        dag_infos=dag_infos,
        task_infos=task_infos,
        task_instances=task_instances,
        dag_runs=dag_runs,
        instance_name=instance_name,
        max_runs_per_batch=max_runs_per_batch,
    )
