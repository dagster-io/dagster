import datetime
import time
from abc import ABC
from collections.abc import Sequence
from typing import Any, Optional

import requests
from dagster import _check as check
from dagster._annotations import beta, public
from dagster._core.definitions.utils import check_valid_name
from dagster._core.errors import DagsterError
from dagster._record import record
from dagster._time import get_current_datetime

from dagster_airlift.core.serialization.serialized_data import DagInfo, TaskInfo

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

    def list_dags(self) -> list["DagInfo"]:
        dag_responses = []
        webserver_url = self.auth_backend.get_webserver_url()
        while True:
            response = self.auth_backend.get_session().get(
                f"{self.get_api_url()}/dags",
                params={"limit": self.dag_list_limit, "offset": len(dag_responses)},
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

    def get_task_instance_batch(
        self, dag_id: str, task_ids: Sequence[str], run_id: str, states: Sequence[str]
    ) -> list["TaskInstance"]:
        """Get all task instances for a given dag_id, task_ids, and run_id."""
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
        end_date_gte: datetime.datetime,
        end_date_lte: datetime.datetime,
        offset: int = 0,
    ) -> tuple[list["DagRun"], int]:
        """For the given list of dag_ids, return a tuple containing:
        - A list of dag runs ending within (end_date_gte, end_date_lte). Returns a maximum of batch_dag_runs_limit (which is configurable on the instance).
        - The number of total rows returned.
        """
        response = self.auth_backend.get_session().post(
            f"{self.get_api_url()}/dags/~/dagRuns/list",
            json={
                "dag_ids": dag_ids,
                "end_date_gte": end_date_gte.isoformat(),
                "end_date_lte": end_date_lte.isoformat(),
                "order_by": "end_date",
                "states": ["success"],
                "page_offset": offset,
                "page_limit": self.batch_dag_runs_limit,
            },
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


@record
class TaskInstance:
    webserver_url: str
    dag_id: str
    task_id: str
    run_id: str
    metadata: dict[str, Any]

    @property
    def state(self) -> str:
        return self.metadata["state"]

    @property
    def note(self) -> str:
        return self.metadata.get("note") or ""

    @property
    def details_url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}/grid?dag_run_id={self.run_id}&task_id={self.task_id}"

    @property
    def log_url(self) -> str:
        return f"{self.details_url}&tab=logs"

    @property
    def logical_date(self) -> datetime.datetime:
        """Returns the airflow-coined "logical date" from the task instance metadata.
        The logical date refers to the starting time of the "data interval" that the overall dag run is processing.
        In airflow < 2.2, this was set as the execution_date parameter in the task instance metadata.
        """
        # In airflow < 2.2, execution_date is set instead of logical_date.
        logical_date_str = check.not_none(
            self.metadata.get("logical_date") or self.metadata.get("execution_date"),
            "Expected one of execution_date or logical_date to be returned from the airflow rest API when querying for task information.",
        )

        return datetime.datetime.fromisoformat(logical_date_str)

    @property
    def start_date(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.metadata["start_date"])

    @property
    def end_date(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.metadata["end_date"])


@record
class DagRun:
    webserver_url: str
    dag_id: str
    run_id: str
    metadata: dict[str, Any]

    @property
    def note(self) -> str:
        return self.metadata.get("note") or ""

    @property
    def url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}/grid?dag_run_id={self.run_id}&tab=details"

    @property
    def success(self) -> bool:
        return self.metadata["state"] == "success"

    @property
    def finished(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def state(self) -> str:
        return self.metadata["state"]

    @property
    def run_type(self) -> str:
        return self.metadata["run_type"]

    @property
    def config(self) -> dict[str, Any]:
        return self.metadata["conf"]

    @property
    def logical_date(self) -> datetime.datetime:
        """Returns the airflow-coined "logical date" from the dag run metadata.
        The logical date refers to the starting time of the "data interval" that the dag run is processing.
        In airflow < 2.2, this was set as the execution_date parameter in the dag run metadata.
        """
        # In airflow < 2.2, execution_date is set instead of logical_date.
        logical_date_str = check.not_none(
            self.metadata.get("logical_date") or self.metadata.get("execution_date"),
            "Expected one of execution_date or logical_date to be returned from the airflow rest API when querying for dag information.",
        )

        return datetime.datetime.fromisoformat(logical_date_str)

    @property
    def start_date(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.metadata["start_date"])

    @property
    def end_date(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self.metadata["end_date"])
