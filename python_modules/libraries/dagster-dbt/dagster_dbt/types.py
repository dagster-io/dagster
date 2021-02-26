from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from dagster import check
from dateutil import parser


class StepTiming(namedtuple("_StepTiming", "name started_at completed_at")):
    """The timing information of an executed step for a dbt node (model).

    Note that users should not construct instances of this class directly. This class is intended to be
    constructed from the JSON output of dbt commands.

    Attributes:
        name (str): The name of the executed step.
        started_at (datetime.datetime): An ISO string timestamp of when the step started executing.
        completed_at (datetime.datetime): An ISO string timestamp of when the step completed
            execution.
    """

    def __new__(cls, name: str, started_at: datetime, completed_at: datetime):
        return super().__new__(
            cls,
            check.str_param(name, "name"),
            check.inst_param(started_at, "started_at", datetime),
            check.inst_param(completed_at, "completed_at", datetime),
        )

    @property
    def duration(self) -> timedelta:
        """datetime.timedelta: The execution duration of the step."""
        return self.completed_at - self.started_at


class NodeResult(
    namedtuple(
        "_NodeResult",
        "node error status execution_time thread_id step_timings table fail warn skip",
    ),
):
    """The result of executing a dbt node (model).

    Note that users should not construct instances of this class directly. This class is intended to be
    constructed from the JSON output of dbt commands.

    Attributes:
        node (Dict[str, Any]): Details about the executed dbt node (model).
        error (Optional[str]): An error message if an error occurred.
        fail (Optional[Any]): The ``fail`` field from the results of the executed dbt node.
        warn (Optional[Any]): The ``warn`` field from the results of the executed dbt node.
        skip (Optional[Any]): The ``skip`` field from the results of the executed dbt node.
        status (Optional[Union[str,int]]): The status of the executed dbt node (model).
        execution_time (float): The execution duration (in seconds) of the dbt node (model).
        thread_id (str): The dbt thread identifier that executed the dbt node (model).
        step_timings (List[StepTiming]): The timings for each step in the executed dbt node
            (model).
        table (Optional[Dict]): Details about the table/view that is created from executing a
            `run_sql <https://docs.getdbt.com/reference/commands/rpc#executing-a-query>`_
            command on an dbt RPC server.
    """

    def __new__(
        cls,
        node: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        status: Optional[Union[str, int]] = None,
        execution_time: Optional[float] = None,
        thread_id: Optional[str] = None,
        step_timings: List[StepTiming] = None,
        table: Optional[Dict[str, Any]] = None,
        fail: Optional[Any] = None,
        warn: Optional[Any] = None,
        skip: Optional[Any] = None,
    ):
        step_timings = check.list_param(step_timings, "step_timings", of_type=StepTiming)
        return super().__new__(
            cls,
            check.opt_dict_param(node, "node", key_type=str),
            check.opt_str_param(error, "error"),
            status,
            check.opt_float_param(execution_time, "execution_time"),
            check.opt_str_param(thread_id, "thread_id"),
            step_timings,
            check.opt_dict_param(table, "table"),
            fail,
            warn,
            skip,
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NodeResult":
        """Constructs an instance of :class:`NodeResult <dagster_dbt.NodeResult>` from a dictionary.

        Args:
            d (Dict[str, Any]): A dictionary with key-values to construct a :class:`NodeResult
                <dagster_dbt.NodeResult>`.

        Returns:
            NodeResult: An instance of :class:`NodeResult <dagster_dbt.NodeResult>`.
        """
        node = check.opt_dict_elem(d, "node")
        error = check.opt_str_elem(d, "error")
        execution_time = check.float_elem(d, "execution_time")
        thread_id = check.opt_str_elem(d, "thread_id")
        check.list_elem(d, "timing")
        step_timings = [
            StepTiming(
                name=d["name"],
                started_at=parser.isoparse(d["started_at"]),
                completed_at=parser.isoparse(d["completed_at"]),
            )
            for d in check.is_list(d["timing"], of_type=Dict)
        ]
        table = check.opt_dict_elem(d, "table")

        return cls(
            step_timings=step_timings,
            node=node,
            error=error,
            execution_time=execution_time,
            thread_id=thread_id,
            table=table,
        )


class DbtResult(namedtuple("_DbtResult", "logs results generated_at elapsed_time")):
    """The results of executing a dbt command.

    Note that users should not construct instances of this class directly. This class is intended to be
    constructed from the JSON output of dbt commands.

    Attributes:
        logs (List[Dict[str, Any]]): JSON log output from the dbt process.
        results (List[NodeResult]]): Details about each executed dbt node (model) in the run.
        generated_at (str): An ISO string timestamp of when the run result was generated by dbt.
        elapsed_time (float): The execution duration (in seconds) of the run.
    """

    def __new__(
        cls,
        logs: List[Dict[str, Any]],
        results: List[NodeResult],
        generated_at: Optional[str] = None,
        elapsed_time: Optional[float] = None,
    ):
        return super().__new__(
            cls,
            check.list_param(logs, "logs", of_type=Dict),
            results,
            check.opt_str_param(generated_at, "generated_at"),
            check.opt_float_param(elapsed_time, "elapsed_time"),
        )

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DbtResult":
        """Constructs an instance of :class:`DbtResult <dagster_dbt.DbtResult>` from a dictionary.

        Args:
            d (Dict[str, Any]): A dictionary with key-values to construct a :class:`DbtResult
                <dagster_dbt.DbtResult>`.

        Returns:
            DbtResult: An instance of :class:`DbtResult <dagster_dbt.DbtResult>`.
        """
        check.list_elem(d, "logs")
        logs = check.is_list(d["logs"], of_type=Dict)
        check.list_elem(d, "results")
        results = [NodeResult.from_dict(d) for d in check.is_list(d["results"], of_type=Dict)]
        generated_at = check.opt_str_elem(d, "generated_at")
        elapsed_time = check.float_elem(d, "elapsed_time")

        return cls(
            logs=logs,
            results=results,
            generated_at=generated_at,
            elapsed_time=elapsed_time,
        )

    def __len__(self) -> int:
        return len(self.results)
