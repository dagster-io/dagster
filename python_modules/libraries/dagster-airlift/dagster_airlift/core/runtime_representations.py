import datetime
from typing import TYPE_CHECKING, Any

from dagster import _check as check
from dagster._record import record

if TYPE_CHECKING:
    from dagster_airlift.core.serialization.serialized_data import DagHandle, TaskHandle


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
    def dag_handle(self) -> "DagHandle":
        from dagster_airlift.core.serialization.serialized_data import DagHandle

        return DagHandle(dag_id=self.dag_id)

    @property
    def url(self) -> str:
        return f"{self.webserver_url}/dags/{self.dag_id}/grid?dag_run_id={self.run_id}&tab=details"

    @property
    def success(self) -> bool:
        return self.metadata["state"] == "success"

    @property
    def finished(self) -> bool:
        from dagster_airlift.core.airflow_instance import TERMINAL_STATES

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

    @property
    def task_handle(self) -> "TaskHandle":
        from dagster_airlift.core.serialization.serialized_data import TaskHandle

        return TaskHandle(dag_id=self.dag_id, task_id=self.task_id)

    @property
    def dag_handle(self) -> "DagHandle":
        from dagster_airlift.core.serialization.serialized_data import DagHandle

        return DagHandle(dag_id=self.dag_id)

    @property
    def try_number(self) -> int:
        return self.metadata["try_number"]
