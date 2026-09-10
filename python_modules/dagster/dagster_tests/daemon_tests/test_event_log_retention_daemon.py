import os
import tempfile
import time
from types import SimpleNamespace

import dagster as dg
from dagster._core.events import DagsterEventType, EngineEventData, StepMaterializationData
from dagster._core.execution.plan.objects import StepSuccessData
from dagster._core.utils import make_new_run_id
from dagster._daemon.event_log_retention import EventLogRetentionDaemon


def _entry(run_id, timestamp, event_type, event_specific_data=None):
    return dg.EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=timestamp,
        dagster_event=dg.DagsterEvent(
            event_type_value=event_type.value,
            job_name="nonce",
            event_specific_data=event_specific_data,
        ),
    )


def test_event_log_retention_daemon_iteration_purges_per_config():
    """One full daemon iteration with retention configured deletes old non-asset rows only."""
    run_id = make_new_run_id()
    old_ts = time.time() - 60 * 60 * 24 * 30  # 30 days ago
    recent_ts = time.time()

    with (
        tempfile.TemporaryDirectory(dir=os.getcwd()) as tmpdir,
        dg.instance_for_test(
            temp_dir=tmpdir,
            overrides={
                "retention": {"event_logs": {"purge_after_days": 7}},
                "event_log_storage": {
                    "module": "dagster._core.storage.event_log",
                    "class": "ConsolidatedSqliteEventLogStorage",
                    "config": {"base_dir": tmpdir},
                },
            },
        ) as instance,
    ):
        instance.store_event(
            _entry(
                run_id,
                old_ts,
                DagsterEventType.ASSET_MATERIALIZATION,
                StepMaterializationData(dg.AssetMaterialization(asset_key=dg.AssetKey("a"))),
            )
        )
        instance.store_event(
            _entry(
                run_id,
                old_ts,
                DagsterEventType.ENGINE_EVENT,
                EngineEventData.in_process(1),
            )
        )
        instance.store_event(
            _entry(
                run_id,
                recent_ts,
                DagsterEventType.STEP_SUCCESS,
                StepSuccessData(duration_ms=1.0),
            )
        )

        list(EventLogRetentionDaemon().run_iteration(SimpleNamespace(instance=instance)))

        remaining = {entry.dagster_event.event_type_value for entry in instance.all_logs(run_id)}
        assert DagsterEventType.ASSET_MATERIALIZATION.value in remaining
        assert DagsterEventType.STEP_SUCCESS.value in remaining
        assert DagsterEventType.ENGINE_EVENT.value not in remaining
