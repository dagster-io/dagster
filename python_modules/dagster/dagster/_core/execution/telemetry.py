from typing import Dict

from dagster._model import DagsterModel
from dagster._serdes import whitelist_for_serdes


@whitelist_for_serdes()
class RunTelemetryData(DagsterModel):
    run_id: str
    datapoints: Dict[str, float]
