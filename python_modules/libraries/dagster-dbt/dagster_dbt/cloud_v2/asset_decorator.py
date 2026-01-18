from collections.abc import Callable
from typing import Any, Optional

from dagster import AssetsDefinition, multi_asset
from dagster._annotations import public
from dagster._core.errors import DagsterInvariantViolationError

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_EXCLUDE_METADATA_KEY,
    DAGSTER_DBT_SELECT_METADATA_KEY,
    DAGSTER_DBT_SELECTOR_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
)
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@public
def dbt_cloud_assets(
    *,
    workspace: DbtCloudWorkspace,
    select: str = DBT_DEFAULT_SELECT,
    exclude: str = DBT_DEFAULT_EXCLUDE,
    selector: str = DBT_DEFAULT_SELECTOR,
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

    specs = workspace.load_asset_specs(
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude,
        selector=selector,
    )

    if any([spec for spec in specs if spec.group_name]) and group_name:
        raise DagsterInvariantViolationError(
            f"Cannot set group_name parameter on dbt_cloud_assets for dbt Cloud workspace with account "
            f"{workspace.account_name}, project {workspace.project_name} and environment {workspace.environment_name} -"
            f" one or more of the dbt Cloud asset specs have a group_name defined."
        )

    return multi_asset(
        name=name,
        group_name=group_name,
        can_subset=True,
        specs=specs,
        op_tags=op_tags,
        check_specs=workspace.load_check_specs(
            dagster_dbt_translator=dagster_dbt_translator,
            select=select,
            exclude=exclude,
            selector=selector,
        ),
    )
