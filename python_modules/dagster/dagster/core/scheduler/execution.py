from collections import namedtuple

from dagster import check
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


class ScheduledExecutionResult:
    pass


@whitelist_for_serdes
class ScheduledExecutionSkipped(
    namedtuple("_ScheduledExecutionSkipped", ""), ScheduledExecutionResult
):
    pass


@whitelist_for_serdes
class ScheduledExecutionFailed(
    namedtuple("_ScheduledExecutionFailed", "run_id errors"), ScheduledExecutionResult
):
    def __new__(cls, run_id, errors):
        return super(ScheduledExecutionFailed, cls).__new__(
            cls,
            run_id=check.opt_str_param(run_id, "run_id"),
            errors=check.list_param(errors, "errors", of_type=SerializableErrorInfo),
        )


@whitelist_for_serdes
class ScheduledExecutionSuccess(
    namedtuple("_ScheduledExecutionSuccess", "run_id"), ScheduledExecutionResult
):
    def __new__(cls, run_id):
        return super(ScheduledExecutionSuccess, cls).__new__(
            cls, run_id=check.str_param(run_id, "run_id")
        )
