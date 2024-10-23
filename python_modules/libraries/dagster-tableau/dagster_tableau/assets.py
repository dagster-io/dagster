from typing import Optional, Sequence, cast

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    AssetSpec,
    ObserveResult,
    Output,
    multi_asset,
)

from dagster_tableau.resources import BaseTableauWorkspace


def build_tableau_executable_assets_definition(
    resource_key: str,
    workspace: BaseTableauWorkspace,
    specs: Sequence[AssetSpec],
    refreshable_workbook_ids: Optional[Sequence[str]] = None,
) -> AssetsDefinition:
    @multi_asset(
        name=f"tableau_sync_site_{workspace.site_name.replace('-', '_')}",
        compute_kind="tableau",
        can_subset=False,
        specs=specs,
        required_resource_keys={resource_key},
    )
    def asset_fn(context: AssetExecutionContext):
        tableau = cast(workspace.__class__, getattr(context.resources, resource_key))
        with tableau.get_client() as client:
            refreshed_workbooks = set()
            for refreshable_workbook_id in refreshable_workbook_ids:
                refreshed_workbooks.add(client.refresh_and_poll(refreshable_workbook_id))
            for spec in specs:
                data = client.get_view(spec.metadata.get("id"))
                asset_key = spec.key
                if (
                    spec.metadata.get("workbook_id")
                    and spec.metadata.get("workbook_id") in refreshed_workbooks
                ):
                    yield Output(
                        value=None,
                        output_name="__".join(asset_key.path),
                        metadata={
                            "workbook_id": data.workbook_id,
                            "owner_id": data.owner_id,
                            "name": data.name,
                            "contentUrl": data.content_url,
                            "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S")
                            if data.created_at
                            else None,
                            "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
                            if data.updated_at
                            else None,
                        },
                    )
                else:
                    yield ObserveResult(
                        asset_key=asset_key,
                        metadata={
                            "workbook_id": data.workbook_id,
                            "owner_id": data.owner_id,
                            "name": data.name,
                            "contentUrl": data.content_url,
                            "createdAt": data.created_at.strftime("%Y-%m-%dT%H:%M:%S")
                            if data.created_at
                            else None,
                            "updatedAt": data.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
                            if data.updated_at
                            else None,
                        },
                    )

    return asset_fn
