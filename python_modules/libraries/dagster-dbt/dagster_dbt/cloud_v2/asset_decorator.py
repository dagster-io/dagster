from typing import Any, Callable, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import preview

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
)
from dagster_dbt.cloud_v2.resources import (
    DBT_CLOUD_DEFAULT_EXCLUDE,
    DBT_CLOUD_DEFAULT_SELECT,
    DBT_CLOUD_DEFAULT_SELECTOR,
    DbtCloudWorkspace,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@preview
def dbt_cloud_assets(
    *,
    workspace: DbtCloudWorkspace,
    select: str = DBT_CLOUD_DEFAULT_SELECT,
    exclude: str = DBT_CLOUD_DEFAULT_EXCLUDE,
    selector: str = DBT_CLOUD_DEFAULT_SELECTOR,
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
        selector (str): A dbt selector to select resources to materialize. Defaults to "".
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
        DAGSTER_DBT_SELECTOR_METADATA_KEY: selector,
    }

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=workspace.load_asset_specs(
            dagster_dbt_translator=dagster_dbt_translator,
            select=select,
            exclude=exclude,
            selector=selector,
        ),
        op_tags=op_tags,
        check_specs=workspace.load_check_specs(
            dagster_dbt_translator=dagster_dbt_translator,
            select=select,
            exclude=exclude,
            selector=selector,
        ),
    )
