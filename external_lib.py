from typing import Optional

from dagster import AssetMaterialization, DagsterInstance
from dagster._core.definitions.events import AssetObservation
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    StepMaterializationData,
)


# This is used by external computations to report materializations
# Right now this hits the DagsterInstance directly, but we would
# change this to hit the Dagster GraphQL API, a REST API, or some
# sort of ext-esque channel
def report_asset_materialization(
    asset_materialization: AssetMaterialization,
    instance: Optional[DagsterInstance] = None,
    run_id: Optional[str] = None,
    job_name: Optional[str] = None,
):
    instance = instance or DagsterInstance.get()
    dagster_event = DagsterEvent.from_external(
        event_type=DagsterEventType.ASSET_MATERIALIZATION,
        event_specific_data=StepMaterializationData(asset_materialization),
        job_name=job_name,
    )
    instance.report_dagster_event(dagster_event, run_id=run_id or "runless")


def report_asset_observation(
    asset_observation: AssetObservation,
    instance: Optional[DagsterInstance] = None,
    run_id: Optional[str] = None,
    job_name: Optional[str] = None,
):
    instance = instance or DagsterInstance.get()
    dagster_event = DagsterEvent.from_external(
        event_type=DagsterEventType.ASSET_OBSERVATION,
        event_specific_data=AssetObservationData(asset_observation),
        job_name=job_name,
    )
    instance.report_dagster_event(dagster_event, run_id=run_id or "runless")
