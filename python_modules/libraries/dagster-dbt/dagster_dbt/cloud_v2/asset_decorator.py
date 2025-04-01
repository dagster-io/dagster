from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import preview

from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@preview
def dbt_cloud_assets(
    *,
    workspace: DbtCloudWorkspace,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to compute a set of dbt Cloud resources,
    described by a manifest.json for a given dbt Cloud workspace.

    Args:
        workspace (DbtCloudWorkspace): The dbt Cloud workspace.
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_dbt_translator (Optional[DagsterDbtTranslator], optional): The translator to use
            to convert dbt Cloud content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterDbtTranslator`.
    """
    dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=workspace.load_asset_specs(
            dagster_dbt_translator=dagster_dbt_translator,
        ),
    )
