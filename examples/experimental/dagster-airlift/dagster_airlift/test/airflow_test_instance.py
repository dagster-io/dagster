from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
        dag_infos: List[DagInfo],
        task_infos: List[TaskInfo],
        task_instances: List[TaskInstance],
        dag_runs: List[DagRun],
    ) -> None:
        self._dag_infos_by_dag_id = {dag_info.dag_id: dag_info for dag_info in dag_infos}
        self._task_infos_by_dag_and_task_id = {
            (task_info.dag_id, task_info.task_id): task_info for task_info in task_infos
        }
        self._task_instances_by_dag_and_task_id: Dict[Tuple[str, str], List[TaskInstance]] = (
            defaultdict(list)
        )
        for task_instance in task_instances:
            self._task_instances_by_dag_and_task_id[
                (task_instance.dag_id, task_instance.task_id)
            ].append(task_instance)
        self._dag_runs_by_dag_id: Dict[str, List[DagRun]] = defaultdict(list)
        for dag_run in dag_runs:
            self._dag_runs_by_dag_id[dag_run.dag_id].append(dag_run)
        self._dag_infos_by_file_token = {dag_info.file_token: dag_info for dag_info in dag_infos}
        super().__init__(
            auth_backend=DummyAuthBackend(),
            name="test_instance",
        )

    def get_dag_runs(self, dag_id: str, start_date: datetime, end_date: datetime) -> List[DagRun]:
        if dag_id not in self._dag_runs_by_dag_id:
            raise ValueError(f"Dag run not found for dag_id {dag_id}")
        return [
            run
            for run in self._dag_runs_by_dag_id[dag_id]
            if start_date.timestamp() <= run.start_date <= end_date.timestamp()
            and start_date.timestamp() <= run.end_date <= end_date.timestamp()
        ]

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

    def get_task_info(self, dag_id, task_id) -> TaskInfo:
        if (dag_id, task_id) not in self._task_infos_by_dag_and_task_id:
            raise ValueError(f"Task info not found for dag_id {dag_id} and task_id {task_id}")
        return self._task_infos_by_dag_and_task_id[(dag_id, task_id)]

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


def make_task_info(dag_id: str, task_id: str) -> TaskInfo:
    return TaskInfo(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        task_id=task_id,
        metadata={},
    )


def make_task_instance(dag_id: str, task_id: str, run_id: str) -> TaskInstance:
    return TaskInstance(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        task_id=task_id,
        run_id=run_id,
        metadata={},
    )


def make_dag_run(dag_id: str, run_id: str, start_date: datetime, end_date: datetime) -> DagRun:
    return DagRun(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        run_id=run_id,
        metadata={
            "state": "success",
            "start_date": AirflowInstance.airflow_date_from_datetime(start_date),
            "end_date": AirflowInstance.airflow_date_from_datetime(end_date),
        },
    )
