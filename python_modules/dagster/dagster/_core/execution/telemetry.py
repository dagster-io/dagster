from dagster._serdes import whitelist_for_serdes
from dagster_shared.dagster_model import DagsterModel


@whitelist_for_serdes()
class RunTelemetryData(DagsterModel):
    run_id: str
    datapoints: dict[str, float]
