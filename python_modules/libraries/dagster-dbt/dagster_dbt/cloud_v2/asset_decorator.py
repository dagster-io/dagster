from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import preview

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
)
from dagster_dbt.cloud_v2.resources import (
    DBT_CLOUD_DEFAULT_EXCLUDE,
    DBT_CLOUD_DEFAULT_SELECT,
    DbtCloudWorkspace,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@preview
def dbt_cloud_assets(
    *,
    workspace: DbtCloudWorkspace,
    select: str = DBT_CLOUD_DEFAULT_SELECT,
    exclude: str = DBT_CLOUD_DEFAULT_EXCLUDE,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a definition for how to compute a set of dbt Cloud resources,
    described by a manifest.json for a given dbt Cloud workspace.

    Args:
        workspace (DbtCloudWorkspace): The dbt Cloud workspace.
        select (str): A dbt selection string for the models in a project that you want
            to include. Defaults to ``fqn:*``.
        exclude (str): A dbt selection string for the models in a project that you want
            to exclude. Defaults to "".
        name (Optional[str], optional): The name of the op.
        group_name (Optional[str], optional): The name of the asset group.
        dagster_dbt_translator (Optional[DagsterDbtTranslator], optional): The translator to use
            to convert dbt Cloud content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterDbtTranslator`.
    """
    dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

    op_tags = {
        DAGSTER_DBT_SELECT_METADATA_KEY: select,
        DAGSTER_DBT_EXCLUDE_METADATA_KEY: exclude,
    }

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=workspace.load_asset_specs(
            dagster_dbt_translator=dagster_dbt_translator,
            select=select,
            exclude=exclude,
        ),
        op_tags=op_tags,
    )
