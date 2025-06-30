from __future__ import annotations

from typing import Iterable, Optional, Sequence

from dagster import AssetKey, AssetsDefinition, SourceAsset, asset, observable_source_asset, AssetObservation
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.external_asset import external_asset_from_spec
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import catalogs


def unity_catalog_assets(
    client: WorkspaceClient,
    *,
    catalog: str,
    schema: Optional[str] = None,
    include_views: bool = True,
    with_lineage: bool = True,
    asset_key_prefix: Sequence[str] = (),
) -> list[AssetsDefinition]:
    """Return Dagster assets representing Unity Catalog tables and views."""

    assets: list[AssetsDefinition] = []
    tables = client.tables.list(catalog_name=catalog, schema_name=schema)
    for table in tables:
        if not include_views and table.table_type == catalogs.TableType.VIEW:
            continue

        key = AssetKey([*asset_key_prefix, catalog, table.schema_name, table.name])
        upstream_keys: list[AssetKey] = []

        if with_lineage and hasattr(client, "lineage"):
            try:
                lineage = client.lineage.get_table_lineage(
                    f"{catalog}.{table.schema_name}.{table.name}"
                )
                if lineage.upstreams:
                    for up in lineage.upstreams:
                        upstream_keys.append(
                            AssetKey([*asset_key_prefix, up.catalog_name, up.schema_name, up.table_name])
                        )
            except Exception:
                pass

        spec = AssetSpec(key=key, deps=upstream_keys)
        assets.append(external_asset_from_spec(spec))

    return assets


def databricks_job_asset(
    job_id: int,
    *,
    name: Optional[str] = None,
    databricks_resource_key: str = "databricks_client",
    poll_interval_seconds: float = 5.0,
    max_wait_time_seconds: float = 24 * 60 * 60,
) -> AssetsDefinition:
    """Create an asset that triggers a Databricks job."""

    asset_name = name or f"databricks_job_{job_id}"

    @asset(name=asset_name, required_resource_keys={databricks_resource_key})
    def _job_asset(context):
        resource = getattr(context.resources, databricks_resource_key)
        run = resource.workspace_client.jobs.run_now(job_id=job_id)
        run_id = run.run_id
        run_url = getattr(run, "run_page_url", None)
        resource.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=poll_interval_seconds,
            max_wait_time_sec=max_wait_time_seconds,
        )
        context.add_output_metadata({"run_id": run_id, "run_url": run_url})

    return _job_asset


def databricks_dlt_pipeline_asset(
    pipeline_id: str,
    *,
    name: Optional[str] = None,
    databricks_resource_key: str = "databricks_client",
    poll_interval_seconds: float = 5.0,
    max_wait_time_seconds: float = 24 * 60 * 60,
) -> AssetsDefinition:
    """Create an asset that triggers a DLT pipeline run."""

    asset_name = name or f"dlt_pipeline_{pipeline_id}"

    @asset(name=asset_name, required_resource_keys={databricks_resource_key})
    def _pipeline_asset(context):
        resource = getattr(context.resources, databricks_resource_key)
        run = resource.workspace_client.pipelines.start_update(pipeline_id=pipeline_id)
        run_id = run.run_id
        run_url = getattr(run, "run_page_url", None)
        resource.wait_for_run_to_complete(
            logger=context.log,
            databricks_run_id=run_id,
            poll_interval_sec=poll_interval_seconds,
            max_wait_time_sec=max_wait_time_seconds,
        )
        context.add_output_metadata({"run_id": run_id, "run_url": run_url})

    return _pipeline_asset


def databricks_job_observable_asset(
    client: WorkspaceClient,
    job_id: int,
    *,
    name: Optional[str] = None,
    asset_key_prefix: Sequence[str] = (),
) -> SourceAsset:
    """Create an observable source asset for a Databricks job."""

    asset_key = AssetKey([*asset_key_prefix, f"job_{job_id}"])

    @observable_source_asset(name=name or asset_key.to_user_string())
    def _observe(context) -> Iterable[AssetObservation]:
        runs = client.jobs.list_runs(job_id=job_id, limit=1)
        latest = runs.runs[0] if runs.runs else None
        if latest:
            yield AssetObservation(
                asset_key=asset_key,
                metadata={
                    "run_id": latest.run_id,
                    "state": getattr(latest.state, "result_state", None)
                    or getattr(latest.state, "life_cycle_state", None),
                    "run_url": latest.run_page_url,
                },
            )

    return _observe


def databricks_dlt_pipeline_observable_asset(
    client: WorkspaceClient,
    pipeline_id: str,
    *,
    name: Optional[str] = None,
    asset_key_prefix: Sequence[str] = (),
) -> SourceAsset:
    """Create an observable source asset for a DLT pipeline."""

    asset_key = AssetKey([*asset_key_prefix, f"dlt_{pipeline_id}"])

    @observable_source_asset(name=name or asset_key.to_user_string())
    def _observe(context) -> Iterable[AssetObservation]:
        updates = client.pipelines.list_updates(pipeline_id=pipeline_id, max_results=1)
        latest = updates.statuses[0] if updates.statuses else None
        if latest:
            yield AssetObservation(
                asset_key=asset_key,
                metadata={
                    "update_id": latest.update_id,
                    "state": latest.state,
                },
            )

    return _observe
