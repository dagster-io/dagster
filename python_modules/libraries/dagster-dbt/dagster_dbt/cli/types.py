from typing import List

import attr

from dagster import usable_as_dagster_type


@usable_as_dagster_type
@attr.s
class DbtCliResult:
    logs: List[dict] = attr.ib()
    return_code: int = attr.ib()  # https://docs.getdbt.com/reference/exit-codes/
    raw_output: str = attr.ib()


@usable_as_dagster_type
@attr.s
class DbtCliStatsResult(DbtCliResult):
    n_pass: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_warn: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_error: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_skip: int = attr.ib(default=None, converter=attr.converters.optional(int))
    n_total: int = attr.ib(default=None, converter=attr.converters.optional(int))
