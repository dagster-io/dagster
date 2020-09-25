from typing import List

import attr

from dagster import usable_as_dagster_type


@usable_as_dagster_type
@attr.s
class DbtCliResult:
    """The result of executing a dbt CLI command.

    Args:
        logs (List[dict]): The JSON logs from the dbt CLI command execution.
        return_code (int): The return code from the process.
        raw_output (str): The raw output of the process.
    """

    logs: List[dict] = attr.ib()
    return_code: int = attr.ib()  # https://docs.getdbt.com/reference/exit-codes/
    raw_output: str = attr.ib()


@usable_as_dagster_type
@attr.s
class DbtCliStatsResult(DbtCliResult):
    """The summary of results of executing a dbt CLI command.

    Args:
        n_pass (int): The number of dbt nodes (models) that passed.
        n_warn (int): The number of dbt nodes (models) that emitted warnings.
        n_error (int): The number of dbt nodes (models) that emitted errors.
        n_skip (int): The number of dbt nodes (models) that were skipped.
        n_total (int): The total number of dbt nodes (models) that were processed.
    """

    n_pass: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_warn: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_error: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_skip: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_total: int = attr.ib(default=None, converter=attr.converters.optional(int))
