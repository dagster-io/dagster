from dagster import AssetKey, job, op
from dagster._core.definitions.asset_checks.asset_check_evaluation import (
    AssetCheckEvaluation,
    AssetCheckEvaluationTargetMaterializationData,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.events import (
    AssetMaterialization,
    AssetMaterializationFailure,
    AssetMaterializationFailureReason,
    AssetMaterializationFailureType,
)
from dagster._core.events import DagsterEvent, DagsterEventType, StepMaterializationData
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.utils import make_new_run_id
from dagster._time import get_current_timestamp

"""
Kind of hacky, but you can add this as a code location to your local cloud and run the job to populate some
failed events in the event log.
To remove the failed events, run:
delete from event_logs_partitioned where dagster_event_type='ASSET_FAILED_TO_MATERIALIZE';
on your local db
"""

asset_keys_succeeding = [AssetKey(["asset_1"]), AssetKey(["asset_5"]), AssetKey(["asset_6"])]
asset_keys_mixed = [AssetKey(["asset_3"])]
asset_keys_failing = [AssetKey(["asset_4"])]
asset_keys_warning_check = [AssetKey(["asset_5"])]
asset_keys_failed_check = [AssetKey(["asset_6"])]


def success_entry(asset_key, instance):
    test_run_id = make_new_run_id()
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


def failure_entry(asset_key, instance):
    test_run_id = make_new_run_id()
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
                failure_type=AssetMaterializationFailureType.FAILED,
                reason=AssetMaterializationFailureReason.FAILED_TO_MATERIALIZE,
            ),
        ),
    )
    instance.store_event(event_to_store)


def asset_check_entry(asset_key: AssetKey, instance: DagsterInstance, severity: AssetCheckSeverity):
    test_run_id = make_new_run_id()
    materialization_record = instance.get_asset_records([asset_key])[
        0
    ].asset_entry.last_materialization_record
    assert materialization_record

    event_to_store = EventLogEntry(
        error_info=None,
        level="debug",
        user_message="",
        run_id=test_run_id,
        timestamp=get_current_timestamp(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_CHECK_EVALUATION.value,
            "nonce",
            event_specific_data=AssetCheckEvaluation(
                asset_key=asset_key,
                check_name=f"{asset_key.to_python_identifier()}_check",
                passed=False,
                metadata={},
                target_materialization_data=AssetCheckEvaluationTargetMaterializationData(
                    storage_id=materialization_record.storage_id,
                    run_id=materialization_record.event_log_entry.run_id,
                    timestamp=materialization_record.event_log_entry.timestamp,
                ),
                severity=severity,
            ),
        ),
    )
    instance.store_event(event_to_store)


@op
def seed_events(context):
    instance = context.instance
    for asset_key in asset_keys_failing:
        failure_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        failure_entry(asset_key, instance)

    for asset_key in asset_keys_mixed:
        success_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        success_entry(asset_key, instance)
        failure_entry(asset_key, instance)
        success_entry(asset_key, instance)
        failure_entry(asset_key, instance)

    for asset_key in asset_keys_succeeding:
        success_entry(asset_key, instance)
        success_entry(asset_key, instance)
        success_entry(asset_key, instance)
        success_entry(asset_key, instance)
        success_entry(asset_key, instance)
        success_entry(asset_key, instance)

    for asset_key in asset_keys_warning_check:
        asset_check_entry(
            asset_key,
            instance,
            AssetCheckSeverity.WARN,
        )

    for asset_key in asset_keys_failed_check:
        asset_check_entry(
            asset_key,
            instance,
            AssetCheckSeverity.ERROR,
        )


@job
def seed_asset_failure_events():
    seed_events()
