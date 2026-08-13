import os
from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock, patch

import dagster as dg
import pytest
from dagster import AssetKey, AssetsDefinition, SensorDefinition
from dagster._utils.test.definitions import scoped_definitions_load_context
from dagster.components.resolved.context import ResolutionContext
from dagster.components.testing import create_defs_folder_sandbox
from dagster.components.utils.defs_state import DefsStateConfigArgs
from dagster_dbt.cloud_v2.component.dbt_cloud_component import (
    DbtCloudComponent,
    DbtCloudJobTriggerDefaults,
)
from dagster_dbt.cloud_v2.resources import DAGSTER_ADHOC_PREFIX, DbtCloudWorkspace
from dagster_dbt.cloud_v2.types import DbtCloudJob, DbtCloudWorkspaceData
from dagster_dbt.components.dbt_component_utils import _set_resolution_context


@pytest.fixture
def mock_workspace_data():
    """Create dummy data mimicking dbt Cloud API response."""
    return DbtCloudWorkspaceData(
        project_id=123,
        environment_id=456,
        adhoc_job_ids=[789],
        manifest={
            "metadata": {
                "dbt_schema_version": "1.0.0",
                "adapter_type": "postgres",
            },
            "nodes": {
                "model.my_project.my_model": {
                    "resource_type": "model",
                    "package_name": "my_project",
                    "path": "my_model.sql",
                    "original_file_path": "models/my_model.sql",
                    "unique_id": "model.my_project.my_model",
                    "fqn": ["my_project", "my_model"],
                    "name": "my_model",
                    "config": {"enabled": True},
                    "tags": [],
                    "depends_on": {"nodes": []},
                    "description": "A test model",
                }
            },
            "sources": {},
            "metrics": {},
            "semantic_models": {},
            "exposures": {},
            "checks": {},
            "child_map": {"model.my_project.my_model": []},
            "parent_map": {"model.my_project.my_model": []},
            "selectors": {},
        },
        jobs=[
            {
                "id": 789,
                "account_id": 111,
                "name": "Adhoc Job",
                "environment_id": 456,
                "project_id": 123,
            }
        ],
    )


@pytest.fixture
def mock_workspace(mock_workspace_data):
    """Mock the DbtCloudWorkspace resource."""
    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data

    mock_invocation = MagicMock()
    mock_invocation.wait.return_value = []
    workspace.cli.return_value = mock_invocation

    return workspace


def _mirror_workspace(mock_workspace_data):
    """Helper: build a MagicMock workspace bound to `mock_workspace_data`."""
    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data
    return workspace


def test_dbt_cloud_component_mirror_jobs_emits_asset_spec_per_cloud_job(
    tmp_path, mock_workspace_data
):
    """When `mirror_jobs="asset"`, each user-defined dbt Cloud job becomes an
    observable external ``AssetSpec`` with `dbt_cloud_job` kind. Dagster-managed adhoc
    pool jobs are filtered out — they're an internal implementation detail, not
    user-facing surface area. Downstream Dagster assets can attach
    ``AutomationCondition``s to react when the job asset materializes.
    """
    # Two user-defined Cloud jobs alongside the (existing) adhoc pool job.
    mock_workspace_data.jobs.append(
        {
            "id": 790,
            "account_id": 111,
            "name": "Nightly Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    mock_workspace_data.jobs.append(
        {
            "id": 791,
            "account_id": 111,
            "name": "Slim CI",
            "environment_id": 456,
            "project_id": 123,
        }
    )

    workspace = _mirror_workspace(mock_workspace_data)

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="asset",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    all_specs = list(defs.resolve_all_asset_specs())
    job_specs = [spec for spec in all_specs if spec.kinds and "dbt_cloud_job" in spec.kinds]
    assert len(job_specs) == 2, [spec.key.to_user_string() for spec in job_specs]

    # Keys are prefixed with `dbt_cloud_job` and use case-preserving sanitized names.
    keys = {spec.key.to_user_string() for spec in job_specs}
    assert "dbt_cloud_job/Nightly_Build" in keys
    assert "dbt_cloud_job/Slim_CI" in keys
    # Adhoc job (id 789) is filtered — not user-facing.
    assert not any(spec.metadata.get("dagster_dbt/cloud_job_id") == 789 for spec in job_specs)

    # Metadata carries the raw dbt Cloud job id and name for downstream navigation.
    metadata_by_key = {spec.key.to_user_string(): spec.metadata for spec in job_specs}
    assert metadata_by_key["dbt_cloud_job/Nightly_Build"]["dagster_dbt/cloud_job_id"] == 790
    assert metadata_by_key["dbt_cloud_job/Nightly_Build"]["dagster_dbt/cloud_job_name"] == (
        "Nightly Build"
    )


def test_dbt_cloud_component_mirror_jobs_filters_dagster_adhoc_pool_by_prefix(
    tmp_path, mock_workspace_data
):
    """Belt-and-suspenders: even if a Dagster adhoc job's id isn't in `adhoc_job_ids`
    (e.g., stale from a previous run), the `DAGSTER_ADHOC_JOB__` name prefix filter
    still excludes it from mirroring.
    """
    mock_workspace_data.jobs.clear()
    mock_workspace_data.jobs.extend(
        [
            {
                "id": 900,
                "account_id": 111,
                "name": f"{DAGSTER_ADHOC_PREFIX}123__456__stale",
                "environment_id": 456,
                "project_id": 123,
            },
            {
                "id": 901,
                "account_id": 111,
                "name": "Prod Build",
                "environment_id": 456,
                "project_id": 123,
            },
        ]
    )
    mock_workspace_data.adhoc_job_ids.clear()  # stale — the name prefix filter must save us

    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="both",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    job_specs = [
        spec
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    ]
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    # Only the user-defined "Prod Build" job should mirror.
    assert [spec.key.to_user_string() for spec in job_specs] == ["dbt_cloud_job/Prod_Build"]
    assert [j.name for j in dagster_jobs] == ["Prod_Build"]


def test_dbt_cloud_component_mirror_jobs_default_off(tmp_path, mock_workspace, mock_workspace_data):
    """`mirror_jobs` defaults to ``"off"`` — no job asset specs and no mirrored @jobs
    (strict backward compatibility for existing users on upgrade).
    """
    component = DbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )
    assert component.mirror_jobs == "off"
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    all_specs = list(defs.resolve_all_asset_specs())
    job_specs = [spec for spec in all_specs if spec.kinds and "dbt_cloud_job" in spec.kinds]
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    assert job_specs == []
    assert dagster_jobs == []


def test_dbt_cloud_component_mirror_jobs_both_emits_asset_specs_and_dagster_jobs(
    tmp_path, mock_workspace_data
):
    """`mirror_jobs="both"` emits BOTH the observable AssetSpec AND the Dagster ``@job``
    per user-defined Cloud job. Users pick which surface they want per use case: assets
    for downstream ``AutomationCondition`` chains, jobs for ``ScheduleDefinition`` or
    ``@run_status_sensor`` wiring.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="both",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    job_specs = [
        spec
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    ]
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    assert len(job_specs) == 1
    assert len(dagster_jobs) == 1
    # Names line up so users can trace across surfaces.
    assert job_specs[0].key.to_user_string() == "dbt_cloud_job/Prod_Build"
    assert dagster_jobs[0].name == "Prod_Build"


def test_dbt_cloud_component_mirror_jobs_job_mode(tmp_path, mock_workspace_data):
    """`mirror_jobs="job"` emits Dagster ``@job``s without asset specs. Users pick this
    when they want scheduling and run-status-sensor semantics but don't need the
    Cloud job to appear as an asset.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="job",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    job_specs = [
        spec
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    ]
    assert [j.name for j in dagster_jobs] == ["Prod_Build"]
    assert job_specs == []


def test_dbt_cloud_component_mirror_jobs_sanitizes_names(tmp_path, mock_workspace_data):
    """Dbt Cloud job names with spaces / dashes / punctuation still produce valid
    ``AssetKey`` segments (``[A-Za-z0-9_]+``). Empty names fall back to
    ``dbt_cloud_job_<id>``. Case is preserved so users can trace back to the Cloud UI.
    """
    mock_workspace_data.jobs.clear()
    mock_workspace_data.jobs.extend(
        [
            {
                "id": 100,
                "account_id": 111,
                "name": "My  Job -- with_special!chars",
                "environment_id": 456,
                "project_id": 123,
            },
            {
                "id": 101,
                "account_id": 111,
                "name": "",
                "environment_id": 456,
                "project_id": 123,
            },
        ]
    )
    mock_workspace_data.adhoc_job_ids.clear()

    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="asset",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    job_keys = {
        spec.key.to_user_string()
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    }
    assert "dbt_cloud_job/My_Job_with_special_chars" in job_keys
    assert "dbt_cloud_job/dbt_cloud_job_101" in job_keys


def test_dbt_cloud_component_mirror_jobs_asset_and_job_keys_align(tmp_path, mock_workspace_data):
    """In `mirror_jobs="both"` mode, the AssetKey used for the job asset and the name
    of the Dagster ``@job`` are derived from the same sanitization so users can trace
    across surfaces. This is what lets the polling sensor emit a materialization for
    the asset when the Dagster @job triggers the Cloud run.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="both",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    job_specs = [
        spec
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    ]
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    # The sanitized name is the same in both surfaces.
    assert job_specs[0].key.path[-1] == dagster_jobs[0].name


def test_dbt_cloud_component_mirror_jobs_deduplicates_colliding_sanitized_names(
    tmp_path, mock_workspace_data
):
    """If two Cloud jobs' names sanitize to the same segment, only one asset spec is
    emitted (later duplicates dropped). This prevents `DuplicateAssetKeyError` from
    tanking the component's defs load in edge cases.
    """
    mock_workspace_data.jobs.clear()
    mock_workspace_data.jobs.extend(
        [
            {
                "id": 100,
                "account_id": 111,
                "name": "Prod Build",
                "environment_id": 456,
                "project_id": 123,
            },
            {
                "id": 101,
                "account_id": 111,
                "name": "Prod  Build",  # sanitizes to same "Prod_Build"
                "environment_id": 456,
                "project_id": 123,
            },
        ]
    )
    mock_workspace_data.adhoc_job_ids.clear()

    workspace = _mirror_workspace(mock_workspace_data)
    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="asset",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    job_specs = [
        spec
        for spec in defs.resolve_all_asset_specs()
        if spec.kinds and "dbt_cloud_job" in spec.kinds
    ]
    assert len(job_specs) == 1


def test_dbt_cloud_component_mirror_jobs_job_op_merges_defaults_with_config(
    tmp_path, mock_workspace_data
):
    """The mirrored Dagster @job's trigger op merges component-level
    ``job_trigger_defaults`` with per-run ``DbtCloudJobTriggerConfig``. Per-run values
    win field-by-field; unset (None) fields are not sent to dbt Cloud so the Cloud
    job's own configured value is used. This gives users explicit, transparent control
    over every override sent to Cloud.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)

    # Capture the exact kwargs sent to trigger_job_run so we can assert on the payload.
    trigger_calls: list[dict[str, Any]] = []

    def _capture_trigger(**kwargs):
        trigger_calls.append(kwargs)
        return {"id": 555}

    workspace.get_client.return_value.trigger_job_run.side_effect = _capture_trigger
    workspace.get_client.return_value.poll_run.return_value = {
        "status": 10,
        "href": "https://cloud.getdbt.com/runs/555",
    }

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="job",
        job_trigger_defaults=DbtCloudJobTriggerDefaults(
            cause="Triggered by Dagster",
            generate_docs_override=True,
            threads_override=8,
        ),
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    assert len(dagster_jobs) == 1

    # Per-run config overrides `threads_override` and adds `git_branch`; other
    # component-level defaults (cause, generate_docs_override) flow through.
    run_config = {
        "ops": {
            "Prod_Build_trigger": {
                "config": {
                    "threads_override": 16,
                    "git_branch": "feature/foo",
                }
            }
        }
    }
    result = dagster_jobs[0].execute_in_process(run_config=run_config)
    assert result.success
    assert len(trigger_calls) == 1
    kwargs = trigger_calls[0]
    assert kwargs["job_id"] == 900
    assert kwargs["cause"] == "Triggered by Dagster"  # default (no per-run override)
    assert kwargs["generate_docs_override"] is True  # default
    assert kwargs["threads_override"] == 16  # per-run wins over default of 8
    assert kwargs["git_branch"] == "feature/foo"  # per-run only, no default
    # Fields that were never set should NOT be in the payload — dbt Cloud uses its
    # configured value for those (that's the "explicit flags" contract).
    for absent in [
        "steps_override",
        "git_sha",
        "schema_override",
        "dbt_version_override",
        "target_name_override",
        "timeout_seconds_override",
    ]:
        assert absent not in kwargs, f"unset override leaked to payload: {absent}"


def test_dbt_cloud_component_mirror_jobs_job_op_no_defaults_only_cause_sent(
    tmp_path, mock_workspace_data
):
    """When no defaults and no per-run config are supplied, the trigger op sends
    nothing except `job_id` — the Cloud job's own configured settings are used.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)
    trigger_calls: list[dict[str, Any]] = []

    def _capture_trigger(**kwargs):
        trigger_calls.append(kwargs)
        return {"id": 555}

    workspace.get_client.return_value.trigger_job_run.side_effect = _capture_trigger
    workspace.get_client.return_value.poll_run.return_value = {
        "status": 10,
        "href": "https://cloud.getdbt.com/runs/555",
    }

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="job",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    result = dagster_jobs[0].execute_in_process()
    assert result.success
    assert trigger_calls == [{"job_id": 900}]


def test_dbt_cloud_component_mirror_jobs_job_op_raises_failure_on_error_status(
    tmp_path, mock_workspace_data
):
    """When a Cloud run finishes with a non-success status (10), the op raises a
    Dagster `Failure` with metadata (run id, status, href) so users see the failure in
    the Dagster run log AND get a click-through to the Cloud run page. Retries,
    alerts, and downstream error propagation flow through normally.
    """
    mock_workspace_data.jobs.append(
        {
            "id": 900,
            "account_id": 111,
            "name": "Prod Build",
            "environment_id": 456,
            "project_id": 123,
        }
    )
    workspace = _mirror_workspace(mock_workspace_data)
    workspace.get_client.return_value.trigger_job_run.return_value = {"id": 555}
    workspace.get_client.return_value.poll_run.return_value = {
        "status": 20,  # ERROR
        "href": "https://cloud.getdbt.com/runs/555",
    }

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        mirror_jobs="job",
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    dagster_jobs = list(defs.jobs) if defs.jobs else []
    result = dagster_jobs[0].execute_in_process(raise_on_error=False)
    assert not result.success


def test_dbt_cloud_job_asset_key_helper():
    """`DbtCloudJob.asset_key()` produces a stable, sanitized key so both the
    component (asset spec) and the sensor (materialization emission) compute the
    same key from the same Cloud job. This is what keeps them wired together.
    """
    job = DbtCloudJob(
        id=42,
        account_id=1,
        project_id=1,
        environment_id=1,
        name="My Cool Job!",
    )
    assert job.sanitized_name() == "My_Cool_Job"
    assert job.asset_key() == AssetKey(["dbt_cloud_job", "My_Cool_Job"])

    unnamed = DbtCloudJob(id=42, account_id=1, project_id=1, environment_id=1, name=None)
    assert unnamed.asset_key() == AssetKey(["dbt_cloud_job", "dbt_cloud_job_42"])


def test_dbt_cloud_component_state_cycle(tmp_path, mock_workspace, mock_workspace_data):
    """Test 1: Full cycle - Write State -> Read State -> Build Defs."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    assert state_path.exists()

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1

    asset_def = assets[0]
    assert isinstance(asset_def, AssetsDefinition)
    assert asset_def.node_def.name == "dbt_cloud_assets"


def test_dbt_cloud_component_state_manifest_tags_models(tmp_path, mock_workspace_data):
    """When `state_manifest_path` is set, model specs get `dbt/state=modified|unchanged|new`
    tags based on checksum comparison. Only SQL-body changes are detected (mirrors dbt's
    `state:modified.sql`); users needing full `state:modified` semantics should use
    `dbt ls --state <path> --select state:modified` at CI time.
    """
    import json

    # Add checksums to the model node so comparison is meaningful. Also add a NEW model
    # that doesn't exist in the state manifest so we can verify the `new` case.
    mock_workspace_data.manifest["nodes"]["model.my_project.my_model"]["checksum"] = {
        "name": "sha256",
        "checksum": "current-hash",
    }
    mock_workspace_data.manifest["nodes"]["model.my_project.brand_new_model"] = {
        "resource_type": "model",
        "package_name": "my_project",
        "path": "brand_new_model.sql",
        "original_file_path": "models/brand_new_model.sql",
        "unique_id": "model.my_project.brand_new_model",
        "fqn": ["my_project", "brand_new_model"],
        "name": "brand_new_model",
        "config": {"enabled": True},
        "tags": [],
        "depends_on": {"nodes": []},
        "description": "",
        "checksum": {"name": "sha256", "checksum": "brand-new-hash"},
    }
    mock_workspace_data.manifest["child_map"]["model.my_project.brand_new_model"] = []
    mock_workspace_data.manifest["parent_map"]["model.my_project.brand_new_model"] = []

    # Write a state manifest with a *different* checksum for my_model, and no
    # brand_new_model entry.
    state_manifest = {
        "nodes": {
            "model.my_project.my_model": {
                "resource_type": "model",
                "unique_id": "model.my_project.my_model",
                "name": "my_model",
                "checksum": {"name": "sha256", "checksum": "prod-hash"},
            }
        }
    }
    state_path_file = tmp_path / "prod_manifest.json"
    state_path_file.write_text(json.dumps(state_manifest))

    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        state_manifest_path=str(state_path_file),
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    all_specs = list(defs.resolve_all_asset_specs())
    specs_by_str = {spec.key.to_user_string(): spec for spec in all_specs}

    # my_model has a different checksum in state -> modified.
    assert specs_by_str["my_model"].tags.get("dbt/state") == "modified"
    # brand_new_model doesn't exist in state -> new.
    assert specs_by_str["brand_new_model"].tags.get("dbt/state") == "new"


def test_dbt_cloud_component_emits_exposure_assets(tmp_path, mock_workspace_data):
    """Dbt Cloud manifests that declare exposures should get corresponding observable
    external `AssetSpec` objects when `enable_exposure_assets=True`. Deps on referenced
    models flow through so the graph shows a materialization -> consumption chain.
    """
    mock_workspace_data.manifest["exposures"] = {
        "exposure.my_project.my_dash": {
            "resource_type": "exposure",
            "unique_id": "exposure.my_project.my_dash",
            "name": "my_dash",
            "package_name": "my_project",
            "fqn": ["my_project", "my_dash"],
            "type": "dashboard",
            "description": "a critical dashboard",
            "url": "https://tableau.example.com/my_dash",
            "maturity": "high",
            "owner": {"email": "team@example.com"},
            "tags": ["priority"],
            "meta": {},
            "config": {},
            "depends_on": {"nodes": ["model.my_project.my_model"]},
        }
    }
    mock_workspace_data.manifest["child_map"]["exposure.my_project.my_dash"] = []
    mock_workspace_data.manifest["parent_map"]["exposure.my_project.my_dash"] = [
        "model.my_project.my_model"
    ]

    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        translation_settings={"enable_exposure_assets": True},  # type: ignore
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    all_specs = list(defs.resolve_all_asset_specs())
    specs_by_str = {spec.key.to_user_string(): spec for spec in all_specs}

    assert "my_dash" in specs_by_str, list(specs_by_str)
    exposure_spec = specs_by_str["my_dash"]
    assert exposure_spec.kinds == {"dashboard"}
    dep_keys = {dep.asset_key for dep in exposure_spec.deps}
    assert dg.AssetKey("my_model") in dep_keys


def test_dbt_cloud_component_emits_source_assets(tmp_path, mock_workspace_data):
    """Dbt Cloud manifests that declare sources should get corresponding observable
    external `AssetSpec` objects emitted alongside the model AssetsDefinition, so
    freshness policies, table metadata, and kinds flow into the graph the same way
    they do for `DbtProjectComponent`.
    """
    # Inject a source with freshness config into the mock manifest.
    mock_workspace_data.manifest["sources"] = {
        "source.my_project.jaffle_shop.raw_customers": {
            "resource_type": "source",
            "package_name": "my_project",
            "unique_id": "source.my_project.jaffle_shop.raw_customers",
            "source_name": "jaffle_shop",
            "name": "raw_customers",
            "fqn": ["my_project", "jaffle_shop", "raw_customers"],
            "database": "db",
            "schema": "raw",
            "identifier": "raw_customers",
            "freshness": {
                "warn_after": {"count": 12, "period": "hour"},
                "error_after": {"count": 24, "period": "hour"},
            },
            "loaded_at_field": "loaded_at",
            "meta": {},
            "tags": [],
            "columns": {},
            "config": {},
            "depends_on": {"nodes": []},
        }
    }
    mock_workspace_data.manifest["child_map"]["source.my_project.jaffle_shop.raw_customers"] = []
    mock_workspace_data.manifest["parent_map"]["source.my_project.jaffle_shop.raw_customers"] = []

    workspace = MagicMock(spec=DbtCloudWorkspace)
    workspace.unique_id = "123-456"
    workspace.project_id = 123
    workspace.environment_id = 456
    workspace.credentials = MagicMock(account_id=999)
    workspace.fetch_workspace_data.return_value = mock_workspace_data
    workspace.get_or_fetch_workspace_data.return_value = mock_workspace_data

    component = DbtCloudComponent(
        workspace=workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
        # Opt in — both defaults are False for backward compatibility.
        translation_settings={  # type: ignore
            "enable_source_assets": True,
            "enable_source_freshness_policies": True,
        },
    )
    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    defs = component.build_defs_from_state(MagicMock(), state_path)
    all_specs = list(defs.resolve_all_asset_specs())
    keys_by_str = {spec.key.to_user_string(): spec for spec in all_specs}

    # Source spec emitted with the derived freshness policy from sources.freshness.
    source_key = "jaffle_shop/raw_customers"
    assert source_key in keys_by_str, list(keys_by_str)
    source_spec = keys_by_str[source_key]
    assert source_spec.freshness_policy is not None


def test_dbt_cloud_component_execution(mock_workspace):
    """Test 2: Execution calls the workspace CLI correctly with configured args."""
    component = DbtCloudComponent(
        workspace=mock_workspace, cli_args=["build", "--select", "tag:staging"]
    )

    context = MagicMock()
    context.has_partition_key = False
    context.has_partition_key_range = False

    dummy_resolution_context = ResolutionContext.default()

    with _set_resolution_context(dummy_resolution_context):
        iterator = component.execute(context)
        list(iterator)

    mock_workspace.cli.assert_called_once()
    call_args = mock_workspace.cli.call_args[1]
    assert call_args["args"] == ["build", "--select", "tag:staging"]


BASIC_DBT_CLOUD_COMPONENT_BODY: dict[str, Any] = {
    "type": "dagster_dbt.DbtCloudComponent",
    "attributes": {
        "workspace": {
            "account_id": 123456,
            "token": "test-token",
            "access_url": "https://cloud.getdbt.com",
            "project_id": 11111,
            "environment_id": 22222,
        },
        "select": "tag:dagster",
    },
}


def test_dbt_cloud_component_from_yaml(mock_workspace_data):
    """Test that DbtCloudComponent can be loaded from YAML configuration."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=BASIC_DBT_CLOUD_COMPONENT_BODY,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert isinstance(component.workspace, DbtCloudWorkspace)
            assert component.workspace.credentials.account_id == 123456
            assert component.workspace.credentials.token == "test-token"
            assert component.workspace.credentials.access_url == "https://cloud.getdbt.com"
            assert component.workspace.project_id == 11111
            assert component.workspace.environment_id == 22222
            assert component.select == "tag:dagster"


def test_dbt_cloud_component_from_yaml_with_env_vars(mock_workspace_data):
    """Test that DbtCloudComponent resolves Jinja env var templates from YAML."""
    body = {
        "type": "dagster_dbt.DbtCloudComponent",
        "attributes": {
            "workspace": {
                "account_id": 123456,
                "token": "{{ env.DBT_CLOUD_TOKEN }}",
                "project_id": 11111,
                "environment_id": 22222,
            },
        },
    }
    with (
        patch.dict(os.environ, {"DBT_CLOUD_TOKEN": "my-secret-token"}),
        create_defs_folder_sandbox() as sandbox,
    ):
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.workspace.credentials.token == "my-secret-token"


def test_dbt_cloud_component_create_sensor(tmp_path, mock_workspace, mock_workspace_data):
    """Test that create_sensor=True includes a SensorDefinition in the built defs."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        create_sensor=True,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)

    sensors = list(defs.sensors) if defs.sensors else []
    assert len(sensors) == 1
    assert isinstance(sensors[0], SensorDefinition)


def test_dbt_cloud_component_sensor_included_by_default(
    tmp_path, mock_workspace, mock_workspace_data
):
    """Test that create_sensor defaults to True and a sensor is included."""
    component = DbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    assert component.create_sensor is True

    state_path = tmp_path / "dbt_cloud_state.json"
    component.write_state_to_path(state_path)

    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    sensors = list(defs.sensors) if defs.sensors else []
    assert len(sensors) == 1
    assert isinstance(sensors[0], SensorDefinition)


def test_dbt_cloud_component_from_yaml_with_sensor(mock_workspace_data):
    """Test that create_sensor can be set via YAML configuration."""
    body = {
        **BASIC_DBT_CLOUD_COMPONENT_BODY,
        "attributes": {
            **BASIC_DBT_CLOUD_COMPONENT_BODY["attributes"],
            "create_sensor": True,
        },
    }
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.create_sensor is True


def test_dbt_cloud_component_translation_none_by_default(mock_workspace_data):
    """Test that translation is None by default and does not alter asset specs."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=BASIC_DBT_CLOUD_COMPONENT_BODY,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.translation is None


def test_dbt_cloud_component_translation_group_name_yaml(mock_workspace_data):
    """Test that the translation YAML block is parsed and the resolved fn applies correctly."""
    body = {
        **BASIC_DBT_CLOUD_COMPONENT_BODY,
        "attributes": {
            **BASIC_DBT_CLOUD_COMPONENT_BODY["attributes"],
            "translation": {
                "group_name": "{{ node.fqn[1] if node.fqn|length > 1 else 'default' }}",
            },
        },
    }
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=DbtCloudComponent,
            defs_yaml_contents=body,
        )
        with (
            scoped_definitions_load_context(),
            sandbox.load_component_and_build_defs(defs_path=defs_path) as (component, _defs),
        ):
            assert isinstance(component, DbtCloudComponent)
            assert component.translation is not None

            # Call the resolved Jinja2 translation fn directly to verify it works
            # without hitting the real dbt Cloud API.
            base_spec = dg.AssetSpec(key=dg.AssetKey("my_model"))
            result = component.translation(base_spec, {"fqn": ["my_project", "my_model"]})
            assert result.group_name == "my_model"

            result_default = component.translation(base_spec, {"fqn": ["my_project"]})
            assert result_default.group_name == "default"


def test_dbt_cloud_component_translation_applies_to_asset_specs(
    tmp_path, mock_workspace, mock_workspace_data
):
    """Test that a translation fn is applied when building defs from state."""

    def my_translation(base_spec: dg.AssetSpec, dbt_props: Mapping[str, Any]) -> dg.AssetSpec:
        fqn = dbt_props.get("fqn", [])
        return base_spec.replace_attributes(group_name=fqn[1] if len(fqn) > 1 else "default")

    component = DbtCloudComponent(
        workspace=mock_workspace,
        translation=my_translation,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "state.json"
    component.write_state_to_path(state_path)
    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)
    spec = next(iter(assets[0].specs))
    # fqn for "model.my_project.my_model" is ["my_project", "my_model"] -> fqn[1] = "my_model"
    assert spec.group_name == "my_model"


def test_dbt_cloud_component_subclass_get_asset_spec(tmp_path, mock_workspace, mock_workspace_data):
    """Test that a subclass can override get_asset_spec to customise asset specs."""

    class CustomDbtCloudComponent(DbtCloudComponent):
        def get_asset_spec(self, manifest, unique_id, project) -> dg.AssetSpec:
            base_spec = super().get_asset_spec(manifest, unique_id, project)
            return base_spec.replace_attributes(
                tags={**base_spec.tags, "custom_tag": "custom_value"}
            )

    component = CustomDbtCloudComponent(
        workspace=mock_workspace,
        defs_state=DefsStateConfigArgs.local_filesystem(),
    )

    state_path = tmp_path / "state.json"
    component.write_state_to_path(state_path)
    mock_load_context = MagicMock()
    defs = component.build_defs_from_state(mock_load_context, state_path)

    assets = list(defs.assets) if defs.assets else []
    assert len(assets) == 1
    assert isinstance(assets[0], AssetsDefinition)
    spec = next(iter(assets[0].specs))
    assert spec.tags.get("custom_tag") == "custom_value"
