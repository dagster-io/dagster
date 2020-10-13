from collections import namedtuple
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union

from dateutil import parser

from dagster import check


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

    def __new__(cls, *, name: str, started_at: str, completed_at: str, **_):
        return super().__new__(
            cls,
            check.str_param(name, "name"),
            parser.isoparse(started_at),
            parser.isoparse(completed_at),
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
        *,
        node: Dict[str, Any],
        error: Optional[str] = None,
        status: Optional[Union[str, int]] = None,
        execution_time: Optional[float] = None,
        thread_id: Optional[str] = None,
        step_timings: List[Dict[str, Any]],
        table: Optional[Dict[str, Any]] = None,
        fail: Optional[Any] = None,
        warn: Optional[Any] = None,
        skip: Optional[Any] = None,
        **_,
    ):
        step_timings = [
            StepTiming(**d) for d in check.list_param(step_timings, "step_timings", of_type=Dict)
        ]
        return super().__new__(
            cls,
            check.dict_param(node, "node", key_type=str),
            check.opt_str_param(error, "error"),
            status,
            check.opt_float_param(execution_time, "execution_time"),
            check.opt_str_param(thread_id, "thread_id"),
            step_timings,
            check.opt_list_param(table, "table", of_type=Dict[str, Any]),
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
        check.dict_elem(d, "node")
        check.opt_str_elem(d, "error")
        check.float_elem(d, "execution_time")
        check.opt_str_elem(d, "thread_id")
        check.list_elem(d, "timing")
        check.is_list(d["timing"], of_type=Dict)
        check.opt_dict_elem(d, "table")

        return cls(step_timings=d.get("timing"), **d)


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
        *,
        logs: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        generated_at: str,
        elapsed_time: Optional[float] = None,
        **_,
    ):
        results = [
            NodeResult.from_dict(d) for d in check.list_param(results, "results", of_type=Dict)
        ]
        return super().__new__(
            cls,
            check.list_param(logs, "logs", of_type=Dict),
            results,
            check.str_param(generated_at, "generated_at"),
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
        check.is_list(d["logs"], of_type=Dict)
        check.list_elem(d, "results")
        check.is_list(d["results"], of_type=Dict)
        check.str_elem(d, "generated_at")
        check.float_elem(d, "elapsed_time")

        return cls(**d)

    def __len__(self) -> int:
        return len(self.results)
