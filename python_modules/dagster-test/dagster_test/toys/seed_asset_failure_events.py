from dagster import AssetKey, job, op
from dagster._core.definitions.events import (
    AssetMaterialization,
    AssetMaterializationFailure,
    AssetMaterializationFailureReason,
)
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.utils import make_new_run_id
from dagster._time import get_current_timestamp

"""
Kind of hacky, but you can add this as a code location to your local cloud and run the job to populate some 
failed events in the event log. 
To remove the failed events, run:
delete from event_logs_partitioned where dagster_event_type='ASSET_FAILED_TO_MATERIALIZE';
on your local db
"""

asset_keys = [AssetKey(["asset_1"]), AssetKey(["asset_2"])]
num_failed_events_per_asset = 1000
num_success_events_per_asset = 1000


@op
def seed_events(context):
    instance = context.instance
    for _ in range(num_failed_events_per_asset):
        test_run_id = make_new_run_id()
        for asset_key in asset_keys:
            event_to_store = EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=get_current_timestamp(),
                dagster_event=DagsterEvent.build_asset_failed_to_materialize_event(
                    job_name="the_job",
                    step_key="the_step",
                    asset_materialization_failure=AssetMaterializationFailure(
                        asset_key=asset_key,
                        partition=None,
                        reason=AssetMaterializationFailureReason.COMPUTE_FAILED,
                    ),
                ),
            )
            instance.store_event(event_to_store)

    for _ in range(num_success_events_per_asset):
        test_run_id = make_new_run_id()
        for asset_key in asset_keys:
            event_to_store = EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=test_run_id,
                timestamp=get_current_timestamp(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION.value,
                    "the_job",
                    event_specific_data=StepMaterializationData(
                        AssetMaterialization(
                            asset_key=asset_key,
                            partition=None,
                        )
                    ),
                ),
            )
            instance.store_event(event_to_store)


@job
def seed_asset_failure_events():
    seed_events()
