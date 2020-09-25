from datetime import datetime, timedelta
from typing import Dict, List, Optional

import attr
import pytz
from dateutil import parser

from dagster import usable_as_dagster_type


def datetime_converter(value):
    if isinstance(value, datetime):
        return value
    elif value is not None:
        return parser.isoparse(value).replace(
            tzinfo=pytz.UTC
        )  # TODO does this need to be dealt with differently in py27? see https://dagster.phacility.com/D2295
    else:
        return None


@attr.s
class NodeTiming(object):
    """The timing of an executed step in a node (model) of a dbt graph.

    Args:
        name (str): The name of the step in the executed dbt node (model).
        started_at (datetime.datetime): A timestamp of when the step started executing.
        completed_at (datetime.datetime): A timestamp of when the step completed execution.
    """

    _name: str = attr.ib()
    _started_at: datetime = attr.ib(converter=datetime_converter)
    _completed_at: datetime = attr.ib(converter=datetime_converter)

    @property
    def name(self):
        """str: The name of the step in the executed dbt node (model)."""
        return self._name

    @property
    def started_at(self):
        """:obj:`datetime.datetime`: A timestamp of when the step started executing."""
        return self._started_at

    @property
    def completed_at(self):
        """:obj:`datetime.datetime`: A timestamp of when the step completed execution."""
        return self._completed_at

    @property
    def duration(self) -> timedelta:
        """:obj:`datetime.timedelta`: The execution duration of the step."""
        return self._completed_at - self._started_at


@attr.s
class NodeResult(object):
    """The result of executing a node (model) in a dbt graph.

    We recommend that you construct an instance of :class:`NodeResult <dagster_dbt.NodeResult>`
    by using the class method :func:`from_result <dagster_dbt.NodeResult.from_result>`.

    Args:
        node (Dict): Details about the executed dbt node (model).
        error (Optional[bool]): Whether an error occurred during execution of the dbt node (model).
        status (str): The status of the executed dbt node (model).
        execution_time (float): The execution duration (in seconds) of the dbt node (model).
        thread_id (str): The dbt thread ID that executed the dbt node (model).
        timing (List[NodeTiming]): The timings for each step in the executed dbt node (model).
        fail (Optional[bool]): Whether the dbt node (model) failed to execute.
        warn (Optional[bool]): Whether the excuted dbt node (model) produced a warning.
        skip (Optional[bool]): Whether execution of the dbt node (model) was skipped.
        table (Optional[Dict]): Details about the table/view that was created by the executed dbt
            node (model).
    """

    _node: Dict = attr.ib()
    _error: Optional[bool] = attr.ib()
    _status: str = attr.ib()
    _execution_time: float = attr.ib()
    _thread_id: str = attr.ib()
    _timing: List[NodeTiming] = attr.ib()
    _fail: Optional[bool] = attr.ib()
    _warn: Optional[bool] = attr.ib()
    _skip: Optional[bool] = attr.ib()
    _table: Optional[Dict] = attr.ib(default=None)

    @classmethod
    def from_result(cls, result):
        """Constructs an instance of :class:`NodeResult <dagster_dbt.NodeResult>` from a dictionary
        ``result``.

        Args:
            result (Dict[str]): The result of a model that was run.

        Returns:
            NodeResult: Returns the constructed :class:`NodeResult <dagster_dbt.NodeResult>`
            instance.
        """
        return cls(
            node=result.get("node"),
            error=result.get("error"),
            status=result.get("status"),
            execution_time=result.get("execution_time"),
            thread_id=result.get("thread_id"),
            timing=[NodeTiming(**step) for step in result.get("timing")],
            fail=result.get("fail"),
            warn=result.get("warn"),
            skip=result.get("skip"),
            table=result.get("table"),
        )

    @property
    def node(self):
        """Dict: Details about the executed dbt node (model)."""
        return self._node

    @property
    def table(self):
        """Optional[Dict]: Details about the table/view that was created by the executed dbt node
        (model).
        """
        return self._table

    @property
    def status(self):
        """str: The status of the executed dbt node (model)."""
        return self._status

    @property
    def error(self):
        """Optional[bool]: True if an error occurred while executing the dbt node (model).
        Otherwise, False or None.
        """
        return self._error

    @property
    def fail(self):
        """Optional[bool]: True if failed to execute the dbt node (model). Otherwise, False or None.
        """
        return self._fail

    @property
    def skip(self):
        """Optional[bool]: True if execution of the dbt node (model) was skipped. Otherwise, False
        or None.
        """
        return self._skip

    @property
    def timing(self):
        """List[NodeTiming]: A list of :class:`NodeTiming <dagster_dbt.NodeTiming>`s for each step
        in the executed dbt node (model)."""
        return self._timing

    @property
    def execution_time(self):
        """float: The execution duration (in seconds) of the dbt node (model)."""
        return self._execution_time


@attr.s
@usable_as_dagster_type
class DbtRpcPollResult(object):
    """The result of a synchronous dbt RPC command.

    We recommend that you construct an instance of :class:`DbtRpcPollResult
    <dagster_dbt.DbtRpcPollResult>` by using the class method :func:`from_results
    <dagster_dbt.DbtRpcPollResult.from_results>`.

    Args:
        state (str): The state of the dbt RPC command.
        start (datetime.datetime): A timestamp of when the dbt RPC command started execution.
        end (datetime.datetime): A timestamp of whent he dbt RPC command ended execution.
        elapsed (float): The duration (in seconds) of the dbt RPC command execution.
        logs (List[Dict]): The JSON logs from the dbt RPC command execution.
        tags (Dict): Additional key-value tags for this dbt RPC command.
        results (List[NodeResult]): The results of each executed dbt node (model) that was executed
            by the dbt RPC command.
        generated_at (Optional[datetime.datetime]): A timestamp of when the dbt RPC command was
            generated.
    """

    _state: str = attr.ib()
    _start: datetime = attr.ib(converter=datetime_converter)
    _end: datetime = attr.ib(converter=datetime_converter)
    _elapsed: float = attr.ib()
    _logs: List[Dict] = attr.ib()
    _tags: Dict = attr.ib()
    _results: List[NodeResult] = attr.ib(factory=list)
    _generated_at: Optional[datetime] = attr.ib(converter=datetime_converter, default=None)
    _elapsed_time: Optional[float] = attr.ib(default=None)
    _success: Optional[bool] = attr.ib(default=None)

    @classmethod
    def from_results(cls, results):
        """Constructs an instance of :class:`DbtRpcPollResult <dagster_dbt.DbtRpcPollResult>` from a
        list of dictionaries `results`. Each dictionary is converted into a :class:`NodeResult
        <dagster_dbt.NodeResult>`, and stored in the `results` property.

        Args:
            results (Dict): The results of each model that was run via a dbt RPC command.

        Returns:
            DbtRpcPollResult: Returns the constructed :class:`DbtRpcPollResult
            <dagster_dbt.DbtRpcPollResult>` instance.
        """

        node_results = []
        if results.get("results") is not None:
            for result in results.get("results"):
                node_results.append(NodeResult.from_result(result))

        return cls(
            state=results.get("state"),
            start=results.get("start"),
            end=results.get("end"),
            elapsed=results.get("elapsed"),
            logs=results.get("logs"),
            tags=results.get("tags"),
            results=node_results,
            generated_at=results.get("generated_at"),
            elapsed_time=results.get("elapsed_time"),
            success=results.get("success"),
        )

    @property
    def results(self):
        """List[NodeResult]: Get or set the list of :class:`NodeResult <dagster_dbt.NodeResult>`s,
        which contain metadata about the execution results of each model that was run.
       """
        return self._results

    def __len__(self):
        return len(self._results)

    def __getitem__(self, position):
        return self._results[position]
