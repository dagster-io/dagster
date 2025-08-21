import datetime
import time
from abc import ABC
from collections.abc import Sequence
from typing import Any, Optional

import requests
from dagster._annotations import beta, public
from dagster._core.definitions.utils import check_valid_name
from dagster._time import get_current_datetime
from dagster_shared.error import DagsterError

from dagster_airlift.core.filter import AirflowFilter
from dagster_airlift.core.runtime_representations import DagRun, TaskInstance
from dagster_airlift.core.serialization.serialized_data import (
    DagInfo,
    Dataset,
    DatasetConsumingDag,
    DatasetProducingTask,
    TaskInfo,
)

TERMINAL_STATES = {"success", "failed", "canceled"}
# This limits the number of task ids that we attempt to query from airflow's task instance rest API at a given time.
# Airflow's batch task instance retrieval rest API doesn't have a limit parameter, but we query a single run at a time, meaning we should be getting
# a single task instance per task id.
# Airflow task instance batch API: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_task_instances_batch
DEFAULT_BATCH_TASK_RETRIEVAL_LIMIT = 100
# This corresponds directly to the page_limit parameter on airflow's batch dag runs rest API.
# Airflow dag run batch API: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html#operation/get_dag_runs_batch
DEFAULT_BATCH_DAG_RUNS_LIMIT = 100
DEFAULT_DAG_LIST_LIMIT = 100
SLEEP_SECONDS = 1


@beta
class AirflowAuthBackend(ABC):
    """An abstract class that represents an authentication backend for an Airflow instance.

    Requires two methods to be implemented by subclasses:
    - get_session: Returns a requests.Session object that can be used to make requests to the Airflow instance, and handles authentication.
    - get_webserver_url: Returns the base URL of the Airflow webserver.

    The `dagster-airlift` package provides the following default implementations:
    - :py:class:`dagster-airlift.core.AirflowBasicAuthBackend`: An authentication backend that uses Airflow's basic auth to authenticate with the Airflow instance.
    - :py:class:`dagster-airlift.mwaa.MwaaSessionAuthBackend`: An authentication backend that uses AWS MWAA's web login token to authenticate with the Airflow instance (requires `dagster-airlift[mwaa]`).
    """

    def get_session(self) -> requests.Session:
        raise NotImplementedError("This method must be implemented by subclasses.")

    def get_webserver_url(self) -> str:
        raise NotImplementedError("This method must be implemented by subclasses.")


@beta
class AirflowInstance:
    """A class that represents a running Airflow Instance and provides methods for interacting with its REST API.

    Args:
        auth_backend (AirflowAuthBackend): The authentication backend to use when making requests to the Airflow instance.
        name (str): The name of the Airflow instance. This will be prefixed to any assets automatically created using this instance.
        batch_task_instance_limit (int): The number of task instances to query at a time when fetching task instances. Defaults to 100.
        batch_dag_runs_limit (int): The number of dag runs to query at a time when fetching dag runs. Defaults to 100.
    """

    def __init__(
        self,
        auth_backend: AirflowAuthBackend,
        name: str,
        batch_task_instance_limit: int = DEFAULT_BATCH_TASK_RETRIEVAL_LIMIT,
        batch_dag_runs_limit: int = DEFAULT_BATCH_DAG_RUNS_LIMIT,
        dag_list_limit: int = DEFAULT_DAG_LIST_LIMIT,
    ) -> None:
        self.auth_backend = auth_backend
        self.name = check_valid_name(name)
        self.batch_task_instance_limit = batch_task_instance_limit
        self.batch_dag_runs_limit = batch_dag_runs_limit
        self.dag_list_limit = dag_list_limit

    @property
    def normalized_name(self) -> str:
        return self.name.replace(" ", "_").replace("-", "_")

    def get_api_url(self) -> str:
        return f"{self.auth_backend.get_webserver_url()}/api/v1"

    def list_dags(self, retrieval_filter: Optional[AirflowFilter] = None) -> list["DagInfo"]:
        retrieval_filter = retrieval_filter or AirflowFilter()
        dag_responses = []
        webserver_url = self.auth_backend.get_webserver_url()

        while True:
            params = retrieval_filter.augment_request_params(
                {
                    "limit": self.dag_list_limit,
                    "offset": len(dag_responses),
                }
            )
            response = self.auth_backend.get_session().get(
                f"{self.get_api_url()}/dags",
                params=params,
            )
            if response.status_code == 200:
                dags = response.json()
                dag_responses.extend(
                    DagInfo(
                        webserver_url=webserver_url,
                        dag_id=dag["dag_id"],
                        metadata=dag,
                    )
                    for dag in dags["dags"]
                )
                if len(dags["dags"]) < self.dag_list_limit:
                    break
            else:
                raise DagsterError(
                    f"Failed to fetch DAGs. Status code: {response.status_code}, Message: {response.text}"
                )
        return dag_responses

    def list_variables(self) -> list[dict[str, Any]]:
        response = self.auth_backend.get_session().get(f"{self.get_api_url()}/variables")
        if response.status_code == 200:
            return response.json()["variables"]
        else:
            raise DagsterError(
                "Failed to fetch variables. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_task_instance_batch_time_range(
        self,
        dag_ids: Sequence[str],
        states: Sequence[str],
        end_date_gte: datetime.datetime,
        end_date_lte: datetime.datetime,
    ) -> list["TaskInstance"]:
        """Get all task instances across all dag_ids for a given time range."""
        response = self.auth_backend.get_session().post(
            f"{self.get_api_url()}/dags/~/dagRuns/~/taskInstances/list",
            json={
                "dag_ids": dag_ids,
                "end_date_gte": end_date_gte.isoformat(),
                "end_date_lte": end_date_lte.isoformat(),
                # Airflow's API refers to this variable in the singular, but it's actually a list. We keep the confusion contained to this one function.
                "state": states,
            },
        )

        if response.status_code != 200:
            raise DagsterError(
                f"Failed to fetch task instances for {dag_ids}. Status code: {response.status_code}, Message: {response.text}"
            )
        return [
            TaskInstance(
                webserver_url=self.auth_backend.get_webserver_url(),
                dag_id=task_instance_json["dag_id"],
                task_id=task_instance_json["task_id"],
                run_id=task_instance_json["dag_run_id"],
                metadata=task_instance_json,
            )
            for task_instance_json in response.json()["task_instances"]
        ]

    def get_task_instance_batch(
        self, dag_id: str, task_ids: Sequence[str], run_id: str, states: Sequence[str]
    ) -> list["TaskInstance"]:
        """Get all task instances for a given dag_id, task_ids, and run_id."""
        # It's not possible to offset the task instance API on versions of Airflow < 2.7.0, so we need to
        # chunk the task ids directly.
        task_instances = []
        task_id_chunks = [
            task_ids[i : i + self.batch_task_instance_limit]
            for i in range(0, len(task_ids), self.batch_task_instance_limit)
        ]
        for task_id_chunk in task_id_chunks:
            response = self.auth_backend.get_session().post(
                f"{self.get_api_url()}/dags/~/dagRuns/~/taskInstances/list",
                json={
                    "dag_ids": [dag_id],
                    "task_ids": task_id_chunk,
                    "dag_run_ids": [run_id],
                },
            )

            if response.status_code == 200:
                for task_instance_json in response.json()["task_instances"]:
                    task_id = task_instance_json["task_id"]
                    task_instance = TaskInstance(
                        webserver_url=self.auth_backend.get_webserver_url(),
                        dag_id=dag_id,
                        task_id=task_id,
                        run_id=run_id,
                        metadata=task_instance_json,
                    )
                    if task_instance.state in states:
                        task_instances.append(task_instance)
            else:
                raise DagsterError(
                    f"Failed to fetch task instances for {dag_id}/{task_id_chunk}/{run_id}. Status code: {response.status_code}, Message: {response.text}"
                )
        return task_instances

    def get_task_instance(self, dag_id: str, task_id: str, run_id: str) -> "TaskInstance":
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}"
        )
        if response.status_code == 200:
            return TaskInstance(
                webserver_url=self.auth_backend.get_webserver_url(),
                dag_id=dag_id,
                task_id=task_id,
                run_id=run_id,
                metadata=response.json(),
            )
        else:
            raise DagsterError(
                f"Failed to fetch task instance for {dag_id}/{task_id}/{run_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_task_infos(self, *, dag_id: str) -> list["TaskInfo"]:
        response = self.auth_backend.get_session().get(f"{self.get_api_url()}/dags/{dag_id}/tasks")

        if response.status_code != 200:
            raise DagsterError(
                f"Failed to fetch task infos for {dag_id}. Status code: {response.status_code}, Message: {response.text}"
            )

        dag_json = response.json()
        webserver_url = self.auth_backend.get_webserver_url()
        return [
            TaskInfo(
                webserver_url=webserver_url,
                dag_id=dag_id,
                metadata=task_data,
                task_id=task_data["task_id"],
            )
            for task_data in dag_json["tasks"]
        ]

    def get_task_info(self, *, dag_id: str, task_id: str) -> "TaskInfo":
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/tasks/{task_id}"
        )
        if response.status_code == 200:
            return TaskInfo(
                webserver_url=self.auth_backend.get_webserver_url(),
                dag_id=dag_id,
                task_id=task_id,
                metadata=response.json(),
            )
        else:
            raise DagsterError(
                f"Failed to fetch task info for {dag_id}/{task_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_dag_source_code(self, file_token: str) -> str:
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dagSources/{file_token}"
        )
        if response.status_code == 200:
            return response.text
        else:
            raise DagsterError(
                f"Failed to fetch source code. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_dag_runs(
        self, dag_id: str, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list["DagRun"]:
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns",
            params={
                "updated_at_gte": start_date.isoformat(),
                "updated_at_lte": end_date.isoformat(),
                "state": ["success"],
            },
        )
        if response.status_code == 200:
            webserver_url = self.auth_backend.get_webserver_url()
            return [
                DagRun(
                    webserver_url=webserver_url,
                    dag_id=dag_id,
                    run_id=dag_run["dag_run_id"],
                    metadata=dag_run,
                )
                for dag_run in response.json()["dag_runs"]
            ]
        else:
            raise DagsterError(
                f"Failed to fetch dag runs for {dag_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    def get_dag_runs_batch(
        self,
        dag_ids: Sequence[str],
        end_date_gte: Optional[datetime.datetime] = None,
        end_date_lte: Optional[datetime.datetime] = None,
        start_date_gte: Optional[datetime.datetime] = None,
        start_date_lte: Optional[datetime.datetime] = None,
        offset: int = 0,
        states: Optional[Sequence[str]] = None,
    ) -> tuple[list["DagRun"], int]:
        """For the given list of dag_ids, return a tuple containing:
        - A list of dag runs ending within (end_date_gte, end_date_lte). Returns a maximum of batch_dag_runs_limit (which is configurable on the instance).
        - The number of total rows returned.
        """
        states = states or ["success"]
        params = {
            "dag_ids": list(dag_ids),
            "order_by": "end_date",
            "states": states,
            "page_offset": offset,
            "page_limit": self.batch_dag_runs_limit,
        }
        if end_date_gte:
            params["end_date_gte"] = end_date_gte.isoformat()
        if end_date_lte:
            params["end_date_lte"] = end_date_lte.isoformat()
        if start_date_gte:
            params["start_date_gte"] = start_date_gte.isoformat()
        if start_date_lte:
            params["start_date_lte"] = start_date_lte.isoformat()

        response = self.auth_backend.get_session().post(
            f"{self.get_api_url()}/dags/~/dagRuns/list",
            json=params,
        )
        if response.status_code == 200:
            webserver_url = self.auth_backend.get_webserver_url()
            return (
                [
                    DagRun(
                        webserver_url=webserver_url,
                        dag_id=dag_run["dag_id"],
                        run_id=dag_run["dag_run_id"],
                        metadata=dag_run,
                    )
                    for dag_run in response.json()["dag_runs"]
                ],
                response.json()["total_entries"],
            )
        else:
            raise DagsterError(
                f"Failed to fetch dag runs for {dag_ids}. Status code: {response.status_code}, Message: {response.text}"
            )

    @public
    def trigger_dag(self, dag_id: str, logical_date: Optional[datetime.datetime] = None) -> str:
        """Trigger a dag run for the given dag_id.

        Does not wait for the run to finish. To wait for the completed run to finish, use :py:meth:`wait_for_run_completion`.

        Args:
            dag_id (str): The dag id to trigger.
            logical_date (Optional[datetime.datetime]): The Airflow logical_date to use for the dag run. If not provided, the current time will be used. Previously known as execution_date in Airflow; find more information in the Airflow docs: https://airflow.apache.org/docs/apache-airflow/stable/faq.html#what-does-execution-date-mean

        Returns:
            str: The dag run id.
        """
        params = {} if not logical_date else {"logical_date": logical_date.isoformat()}
        response = self.auth_backend.get_session().post(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns",
            json=params,
        )
        if response.status_code != 200:
            raise DagsterError(
                f"Failed to launch run for {dag_id}. Status code: {response.status_code}, Message: {response.text}"
            )
        return response.json()["dag_run_id"]

    def get_dag_run(self, dag_id: str, run_id: str) -> "DagRun":
        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns/{run_id}"
        )
        if response.status_code != 200:
            raise DagsterError(
                f"Failed to fetch dag run for {dag_id}/{run_id}. Status code: {response.status_code}, Message: {response.text}"
            )
        return DagRun(
            webserver_url=self.auth_backend.get_webserver_url(),
            dag_id=dag_id,
            run_id=run_id,
            metadata=response.json(),
        )

    def unpause_dag(self, dag_id: str) -> None:
        response = self.auth_backend.get_session().patch(
            f"{self.get_api_url()}/dags",
            json={"is_paused": False},
            params={"dag_id_pattern": dag_id},
        )
        if response.status_code != 200:
            raise DagsterError(
                f"Failed to unpause dag {dag_id}. Status code: {response.status_code}, Message: {response.text}"
            )

    @public
    def wait_for_run_completion(self, dag_id: str, run_id: str, timeout: int = 30) -> None:
        """Given a run ID of an airflow dag, wait for that run to reach a completed state.

        Args:
            dag_id (str): The dag id.
            run_id (str): The run id.
            timeout (int): The number of seconds to wait before timing out.

        Returns:
            None
        """
        start_time = get_current_datetime()
        while get_current_datetime() - start_time < datetime.timedelta(seconds=timeout):
            dag_run = self.get_dag_run(dag_id, run_id)
            if dag_run.finished:
                return
            time.sleep(
                SLEEP_SECONDS
            )  # Sleep for a second before checking again. This way we don't flood the rest API with requests.
        raise DagsterError(f"Timed out waiting for airflow run {run_id} to finish.")

    @public
    def get_run_state(self, dag_id: str, run_id: str) -> str:
        """Given a run ID of an airflow dag, return the state of that run.

        Args:
            dag_id (str): The dag id.
            run_id (str): The run id.

        Returns:
            str: The state of the run. Will be one of the states defined by Airflow.
        """
        return self.get_dag_run(dag_id, run_id).state

    def delete_run(self, dag_id: str, run_id: str) -> None:
        response = self.auth_backend.get_session().delete(
            f"{self.get_api_url()}/dags/{dag_id}/dagRuns/{run_id}"
        )
        if response.status_code != 204:
            raise DagsterError(
                f"Failed to delete run for {dag_id}/{run_id}. Status code: {response.status_code}, Message: {response.text}"
            )
        return None

    def _get_datasets(
        self,
        *,
        limit: int,
        offset: int,
        retrieval_filter: AirflowFilter,
        dag_ids: Optional[Sequence[str]],
    ) -> Sequence["Dataset"]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if retrieval_filter.dataset_uri_ilike:
            params["uri_pattern"] = retrieval_filter.dataset_uri_ilike

        response = self.auth_backend.get_session().get(
            f"{self.get_api_url()}/datasets",
            params=params,
        )

        if response.status_code != 200:
            raise DagsterError(
                f"Failed to fetch datasets. Status code: {response.status_code}, Message: {response.text}"
            )

        data = response.json()
        datasets = []

        for dataset_data in data["datasets"]:
            producing_tasks = [
                DatasetProducingTask(
                    dag_id=task_data["dag_id"],
                    task_id=task_data["task_id"],
                    created_at=task_data.get("created_at", ""),
                    updated_at=task_data.get("updated_at", ""),
                )
                for task_data in dataset_data.get("producing_tasks", [])
                if not dag_ids or task_data["dag_id"] in dag_ids
            ]
            if not producing_tasks:
                # If the dataset has no producers among the set of dag_ids we care about, skip it.
                continue

            consuming_dags = [
                DatasetConsumingDag(
                    dag_id=dag_data["dag_id"],
                    created_at=dag_data.get("created_at", ""),
                    updated_at=dag_data.get("updated_at", ""),
                )
                for dag_data in dataset_data.get("consuming_dags", [])
                # Skip consuming dags that are not in the set of dag_ids we care about.
                if not dag_ids or dag_data["dag_id"] in dag_ids
            ]

            dataset = Dataset(
                id=dataset_data["id"],
                uri=dataset_data["uri"],
                extra=dataset_data.get("extra", {}),
                created_at=dataset_data.get("created_at", ""),
                updated_at=dataset_data.get("updated_at", ""),
                consuming_dags=consuming_dags,
                producing_tasks=producing_tasks,
            )

            datasets.append(dataset)

        return datasets

    def get_all_datasets(
        self,
        *,
        batch_size: int = 100,
        retrieval_filter: Optional[AirflowFilter] = None,
        dag_ids: Optional[Sequence[str]] = None,
    ) -> Sequence["Dataset"]:
        """Get all datasets from the Airflow instance, handling pagination.

        Args:
            batch_size: The number of items to fetch per request. Default is 100.
            retrieval_filter: An optional filter to apply to the dataset retrieval.
            dag_ids: One or more DAG IDs to filter datasets by associated DAGs either consuming or producing.

        Returns:
            A list of Dataset objects.
        """
        datasets = []
        offset = 0
        retrieval_filter = retrieval_filter or AirflowFilter()

        while True:
            batch = self._get_datasets(
                limit=batch_size,
                offset=offset,
                retrieval_filter=retrieval_filter,
                dag_ids=dag_ids,
            )

            datasets.extend(batch)

            if len(batch) < batch_size:  # No more datasets to fetch
                break

            offset += batch_size

        return datasets

    def get_task_instance_logs(
        self, dag_id: str, task_id: str, run_id: str, try_number: int
    ) -> str:
        continuation_token = None
        logs = []
        while True:
            response = self.auth_backend.get_session().get(
                f"{self.get_api_url()}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/{try_number}",
                headers={"Accept": "application/json"},
                params={"token": continuation_token} if continuation_token else None,
                timeout=5,
            )
            if response.status_code != 200:
                raise DagsterError(
                    f"Failed to fetch task instance logs for {dag_id}/{task_id}/{run_id}/{try_number}. Status code: {response.status_code}, Message: {response.text}"
                )
            data = response.json()
            # Love how it's different in the two cases lol.
            continuation_token = data.get("continuation_token")
            log = parse_af_log_response(data["content"])
            logs.append(log)
            if not continuation_token or log == "":
                break
        return "".join(logs)


def parse_af_log_response(logs: str) -> str:
    import ast

    parsed_data: list = ast.literal_eval(logs)
    strs = []
    for log_item in parsed_data:
        strs.append(log_item[1])
    return "".join(strs)
