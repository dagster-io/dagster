from typing import List, NamedTuple

import dagster._check as check
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes()
class TelemetryDataPoint(NamedTuple("_TelemetryDataPoint", [("name", str), ("value", float)])):
    def __new__(cls, name: str, value: float):
        return super(TelemetryDataPoint, cls).__new__(
            cls, name=check.str_param(name, "name"), value=check.float_param(value, "value")
        )


@whitelist_for_serdes()
class RunTelemetryData(
    NamedTuple(
        "_RunTelemetryData",
        [
            ("run_id", str),
            ("datapoints", List[TelemetryDataPoint]),
        ],
    )
):
    def __new__(cls, run_id: str, datapoints: List[TelemetryDataPoint]):
        check.list_param(datapoints, "datapoints", of_type=TelemetryDataPoint)

        return super(RunTelemetryData, cls).__new__(
            cls, run_id=check.str_param(run_id, "run_id"), datapoints=datapoints
        )
