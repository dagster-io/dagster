from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, Optional

import requests

from dagster_airlift.core import AirflowInstance
from dagster_airlift.core.airflow_instance import DagInfo, TaskInfo
from dagster_airlift.core.basic_auth import AirflowAuthBackend
from dagster_airlift.core.filter import AirflowFilter
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance
from dagster_airlift.core.serialization.serialized_data import (
    Dataset,
    DatasetConsumingDag,
    DatasetProducingTask,
)


class DummyAuthBackend(AirflowAuthBackend):
    def get_session(self) -> requests.Session:
        raise NotImplementedError("This shouldn't be called from this mock context.")

    def get_webserver_url(self) -> str:
        return "http://dummy.domain"


DEFAULT_FAKE_INSTANCE_NAME = "test_instance"


class AirflowInstanceFake(AirflowInstance):
    """Loads a set of provided DagInfo, TaskInfo, and TaskInstance objects for testing."""

    def __init__(
        self,
        dag_infos: list[DagInfo],
        task_infos: list[TaskInfo],
        task_instances: list[TaskInstance],
        dag_runs: list[DagRun],
        datasets: list[Dataset] = [],
        variables: list[dict[str, Any]] = [],
        instance_name: Optional[str] = None,
        max_runs_per_batch: Optional[int] = None,
        logs: Optional[Mapping[str, Mapping[str, str]]] = None,
    ) -> None:
        self._dag_infos_by_dag_id = {dag_info.dag_id: dag_info for dag_info in dag_infos}
        self._task_infos_by_dag_and_task_id = {
            (task_info.dag_id, task_info.task_id): task_info for task_info in task_infos
        }
        self._task_instances_by_dag_and_task_id: dict[tuple[str, str], list[TaskInstance]] = (
            defaultdict(list)
        )
        self._logs_by_run_id_and_task_id: dict[tuple[str, str], str] = defaultdict(lambda: "")
        for run_id, task_log_map in (logs or {}).items():
            for task_id, log in task_log_map.items():
                self._logs_by_run_id_and_task_id[(run_id, task_id)] = log

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
        self._datasets = datasets
        super().__init__(
            auth_backend=DummyAuthBackend(),
            name=DEFAULT_FAKE_INSTANCE_NAME if instance_name is None else instance_name,
        )

    def list_dags(self, retrieval_filter: Optional[AirflowFilter] = None) -> list[DagInfo]:
        retrieval_filter = retrieval_filter or AirflowFilter()
        # Very basic filtering for testing purposes
        dags_to_retrieve = list(self._dag_infos_by_dag_id.values())
        if retrieval_filter.dag_id_ilike:
            dags_to_retrieve = [
                dag_info
                for dag_info in dags_to_retrieve
                if retrieval_filter.dag_id_ilike in dag_info.dag_id
            ]
        if retrieval_filter.airflow_tags:
            dags_to_retrieve = [
                dag_info
                for dag_info in dags_to_retrieve
                if all(
                    tag in dag_info.metadata.get("tags", [])
                    for tag in retrieval_filter.airflow_tags
                )
            ]
        return dags_to_retrieve

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

    def _task_instance_flat_list(self) -> list[TaskInstance]:
        return [
            task_instance
            for task_instances in self._task_instances_by_dag_and_task_id.values()
            for task_instance in task_instances
        ]

    def get_dag_runs_batch(
        self,
        dag_ids: Sequence[str],
        end_date_gte: Optional[datetime] = None,
        end_date_lte: Optional[datetime] = None,
        start_date_gte: Optional[datetime] = None,
        start_date_lte: Optional[datetime] = None,
        offset: int = 0,
        states: Optional[Sequence[str]] = None,
    ) -> tuple[list[DagRun], int]:
        if end_date_gte and end_date_lte:
            runs = [
                (run.end_date, run)
                for runs in self._dag_runs_by_dag_id.values()
                for run in runs
                if (states is None or run.state in states)
                and end_date_gte.timestamp() <= run.end_date.timestamp() <= end_date_lte.timestamp()
                and run.dag_id in dag_ids
            ]
        elif start_date_gte and start_date_lte:
            runs = [
                (run.start_date, run)
                for runs in self._dag_runs_by_dag_id.values()
                for run in runs
                if start_date_gte.timestamp()
                <= run.start_date.timestamp()
                <= start_date_lte.timestamp()
                and run.dag_id in dag_ids
                and (states is None or run.state in states)
            ]
        else:
            raise ValueError(
                "Either end_date_gte and end_date_lte or start_date_gte and start_date_lte must be provided."
            )
        sorted_runs = [run for _, run in sorted(runs, key=lambda x: x[0])]
        end_idx = (
            offset + self._max_runs_per_batch if self._max_runs_per_batch else len(sorted_runs)
        )
        return (sorted_runs[offset:end_idx], len(sorted_runs))

    def get_task_instance_batch_time_range(
        self,
        dag_ids: Sequence[str],
        states: Sequence[str],
        end_date_gte: datetime,
        end_date_lte: datetime,
    ) -> list["TaskInstance"]:
        return [
            task_instance
            for task_instance in self._task_instance_flat_list()
            if end_date_gte.timestamp()
            <= task_instance.end_date.timestamp()
            <= end_date_lte.timestamp()
            and task_instance.dag_id in dag_ids
            and task_instance.state in states
        ]

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

    def get_all_datasets(
        self,
        *,
        batch_size=100,
        retrieval_filter: Optional[AirflowFilter] = None,
        dag_ids: Optional[Sequence[str]] = None,
    ) -> Sequence[Dataset]:
        return_datasets = []
        retrieval_filter = retrieval_filter or AirflowFilter()
        for dataset in self._datasets:
            if (
                retrieval_filter.dataset_uri_ilike
                and retrieval_filter.dataset_uri_ilike not in dataset.uri
            ):
                continue
            if dag_ids and not any(t.dag_id in dag_ids for t in dataset.producing_tasks):
                continue
            return_datasets.append(dataset)
        return return_datasets

    def get_task_instance_logs(
        self, dag_id: str, task_id: str, run_id: str, try_number: int
    ) -> str:
        return self._logs_by_run_id_and_task_id[(run_id, task_id)]


def make_dag_info(
    instance_name: str, dag_id: str, file_token: Optional[str], dag_props: Mapping[str, Any]
) -> DagInfo:
    return DagInfo(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        metadata={"file_token": file_token if file_token else "dummy_file_token", **dag_props},
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
    try_number: int = 1,
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
            "try_number": try_number,
        },
    )


def make_dag_run(
    dag_id: str,
    run_id: str,
    start_date: datetime,
    end_date: Optional[datetime],
    logical_date: Optional[datetime] = None,
    state: Optional[str] = None,
) -> DagRun:
    metadata = {
        "state": state or "success",
        "start_date": start_date.isoformat(),
        "logical_date": logical_date.isoformat() if logical_date else start_date.isoformat(),
        "run_type": "manual",
        "note": "dummy note",
        "conf": {},
    }
    if end_date:
        metadata["end_date"] = end_date.isoformat()
    return DagRun(
        webserver_url="http://dummy.domain",
        dag_id=dag_id,
        run_id=run_id,
        metadata=metadata,
    )


def make_dataset(
    producing_tasks: Sequence[Mapping[str, str]],
    consuming_dags: Sequence[str],
    uri: str,
    extra: Mapping[str, Any],
) -> Dataset:
    return Dataset(
        id=1,
        uri=uri,
        extra=extra,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        producing_tasks=[
            DatasetProducingTask(
                dag_id=task["dag_id"],
                task_id=task["task_id"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            for task in producing_tasks
        ],
        consuming_dags=[
            DatasetConsumingDag(
                dag_id=dag_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            for dag_id in consuming_dags
        ],
    )


def make_instance(
    dag_and_task_structure: dict[str, list[str]],
    dataset_construction_info: Sequence[Mapping[str, Any]] = [],
    dag_runs: list[DagRun] = [],
    task_deps: dict[str, list[str]] = {},
    instance_name: Optional[str] = None,
    max_runs_per_batch: Optional[int] = None,
    dag_props: dict[str, Any] = {},
    task_instances: Optional[list[TaskInstance]] = None,
    logs: Optional[Mapping[str, Mapping[str, str]]] = None,
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
        dag_info = make_dag_info(
            instance_name=instance_name or DEFAULT_FAKE_INSTANCE_NAME,
            dag_id=dag_id,
            file_token=dag_id,
            dag_props=dag_props.get(dag_id, {}),
        )
        dag_infos.append(dag_info)
        task_infos.extend(
            [
                make_task_info(
                    dag_id=dag_id, task_id=task_id, downstream_task_ids=task_deps.get(task_id, [])
                )
                for task_id in task_ids
            ]
        )
    if not task_instances:
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
    datasets = []
    for dataset_info in dataset_construction_info:
        datasets.append(
            make_dataset(
                producing_tasks=dataset_info["producing_tasks"],
                consuming_dags=dataset_info["consuming_dags"],
                uri=dataset_info["uri"],
                extra=dataset_info.get("extra", {}),
            )
        )
    return AirflowInstanceFake(
        dag_infos=dag_infos,
        task_infos=task_infos,
        task_instances=task_instances,
        dag_runs=dag_runs,
        instance_name=instance_name,
        max_runs_per_batch=max_runs_per_batch,
        datasets=datasets,
        logs=logs,
    )
