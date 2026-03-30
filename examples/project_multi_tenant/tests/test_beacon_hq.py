from __future__ import annotations

from pathlib import Path

import dagster as dg

from beacon_hq import defs
from beacon_hq.assets.reports import (
    briefing_highlights,
    consolidated_revenue,
    executive_context_packet,
    executive_llm_audit_log,
    executive_summary,
    risk_overview,
)
from beacon_hq.sensors import _orchestration_date_for_run, beacon_after_upstream_success_sensor
from shared.io_managers import make_duckdb_io_manager
from tests.fakes import MockLLMResource


@dg.op
def _noop() -> int:
    return 1


def _make_upstream_job(job_name: str) -> dg.JobDefinition:
    @dg.job(name=job_name)
    def _job() -> None:
        _noop()

    return _job


def _execute_success(
    instance: dg.DagsterInstance,
    *,
    job_name: str,
    tags: dict[str, str] | None = None,
) -> dg.ExecuteInProcessResult:
    result = _make_upstream_job(job_name).execute_in_process(instance=instance, tags=tags)
    assert result.success
    return result


def _build_success_context(
    instance: dg.DagsterInstance,
    result: dg.ExecuteInProcessResult,
) -> dg.RunStatusSensorContext:
    dagster_event = _get_run_success_event(result)
    return dg.build_run_status_sensor_context(
        sensor_name="beacon_after_upstream_success_sensor",
        dagster_instance=instance,
        dagster_run=result.dagster_run,
        dagster_event=dagster_event,
    )


def _get_run_success_event(
    result: dg.ExecuteInProcessResult,
) -> dg.DagsterEvent:
    if hasattr(result, "get_run_success_event"):
        return result.get_run_success_event()

    if hasattr(result, "get_job_success_event"):
        return result.get_job_success_event()

    for event in reversed(result.all_events):
        if getattr(event, "event_type_value", "") == "PIPELINE_SUCCESS":
            return event

    raise AssertionError("Could not find a run success event in the execute_in_process result.")


def test_beacon_hq_definitions_load() -> None:
    asset_keys = defs.resolve_all_asset_keys()
    assert dg.AssetKey(["beacon_hq", "executive_summary"]) in asset_keys
    assert dg.AssetKey(["beacon_hq", "consolidated_revenue"]) in asset_keys
    job_names = {job.name for job in defs.resolve_all_job_defs()}
    assert "beacon_reporting_inputs_job" in job_names
    assert "beacon_executive_briefing_job" in job_names
    sensor = defs.resolve_sensor_def("beacon_after_upstream_success_sensor")
    assert sensor.name == "beacon_after_upstream_success_sensor"


def test_beacon_hq_materializes(tmp_path: Path) -> None:
    result = dg.materialize(
        [
            consolidated_revenue,
            risk_overview,
            briefing_highlights,
            executive_context_packet,
            executive_summary,
            executive_llm_audit_log,
        ],
        resources={
            "llm": MockLLMResource(model_name="gamma-test"),
            "io_manager": make_duckdb_io_manager("beacon_hq_test", base_dir=tmp_path),
        },
    )
    assert result.success
    summary = result.output_for_node("executive_summary")
    assert "summary" in summary.columns


def test_beacon_sensor_waits_for_missing_upstream_job() -> None:
    instance = dg.DagsterInstance.ephemeral()
    harbor_result = _execute_success(
        instance,
        job_name="harbor_catalog_publish_job",
        tags={"orchestration_date": "2026-03-19"},
    )

    response = beacon_after_upstream_success_sensor(_build_success_context(instance, harbor_result))

    assert isinstance(response, dg.SkipReason)
    assert "summit_risk_scoring_job" in response.skip_message


def test_beacon_sensor_accepts_manual_ui_style_runs() -> None:
    instance = dg.DagsterInstance.ephemeral()
    harbor_result = _execute_success(instance, job_name="harbor_catalog_publish_job")
    summit_result = _execute_success(instance, job_name="summit_risk_scoring_job")

    response = beacon_after_upstream_success_sensor(_build_success_context(instance, harbor_result))

    assert isinstance(response, dg.RunRequest)
    assert response.tags is not None
    assert response.tags["tenant"] == "beacon_hq"
    assert response.tags["triggered_by"] == "beacon_after_upstream_success_sensor"
    assert response.tags["orchestration_date"] == _orchestration_date_for_run(
        instance,
        summit_result.dagster_run,
    )
