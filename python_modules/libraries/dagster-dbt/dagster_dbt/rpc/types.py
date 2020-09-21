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
    _name: str = attr.ib()
    _started_at: datetime = attr.ib(converter=datetime_converter)
    _completed_at: datetime = attr.ib(converter=datetime_converter)

    @property
    def name(self):
        return self._name

    @property
    def started_at(self):
        return self._started_at

    @property
    def completed_at(self):
        return self._completed_at

    @property
    def duration(self) -> timedelta:
        return self._completed_at - self._started_at


@attr.s
class NodeResult(object):
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
        return self._node

    @property
    def table(self):
        return self._table

    @property
    def status(self):
        return self._status

    @property
    def error(self):
        return self._error

    @property
    def fail(self):
        return self._fail

    @property
    def skip(self):
        return self._skip

    @property
    def timing(self):
        return self._timing

    @property
    def execution_time(self):
        return self._execution_time


@attr.s
@usable_as_dagster_type
class DbtRpcPollResult(object):
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
        return self._results

    def __len__(self):
        return len(self._results)

    def __getitem__(self, position):
        return self._results[position]
