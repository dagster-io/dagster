import datetime
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from dagster import (
    AssetsDefinition,
    _check as check,
)
from dagster._annotations import beta
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    build_last_update_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.time_partition import (
    build_time_partition_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.utils import (
    DEFAULT_FRESHNESS_SEVERITY,
    asset_to_keys_iterable,
    assets_to_keys,
    ensure_no_duplicate_assets,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster import AssetKey

from dagster_dbt.asset_utils import (
    get_asset_keys_to_resource_props,
    get_manifest_and_translator_from_dbt_assets,
)


@beta
def build_freshness_checks_from_dbt_assets(
    *,
    dbt_assets: Sequence[AssetsDefinition],
) -> Sequence[AssetChecksDefinition]:
    """Returns a sequence of freshness checks constructed from the provided dbt assets.

    Freshness checks can be configured on a per-model basis in the model schema configuration.

    For assets which are not partitioned based on time, the freshness check configuration mirrors
    that of the :py:func:`build_last_update_freshness_checks` function. `lower_bound_delta` is provided in
    terms of seconds, and `deadline_cron` is optional.

    For time-partitioned assets, the freshness check configuration mirrors that of the
    :py:func:`build_time_partition_freshness_checks` function.

    Below is example of configuring a non-time-partitioned dbt asset with a freshness check.
    This code would be placed in the schema.yml file for the dbt model.

    .. code-block:: YAML

        models:
          - name: customers
            ...
            meta:
              dagster:
                freshness_check:
                  lower_bound_delta_seconds: 86400 # 1 day
                  deadline_cron: "0 0 * * *" # Optional
                  severity: "WARN" # Optional, defaults to "WARN"

    Below is an example of configuring a time-partitioned dbt asset with a freshness check.
    This code would be placed in the schema.yml file for the dbt model.

    .. code-block:: yaml

        models:
          - name: customers
            ...
            meta:
              dagster:
                freshness_check:
                  deadline_cron: "0 0 * * *"
                  severity: "WARN" # Optional, defaults to "WARN"

    Args:
        dbt_assets (Sequence[AssetsDefinition]): A sequence of dbt assets to construct freshness
            checks from.

    Returns:
        Sequence[AssetChecksDefinition]: A sequence of asset checks definitions representing the
            freshness checks for the provided dbt assets.
    """
    freshness_checks = []
    dbt_assets = check.sequence_param(dbt_assets, "dbt_assets", AssetsDefinition)
    ensure_no_duplicate_assets(dbt_assets)
    asset_key_to_assets_def: dict[AssetKey, AssetsDefinition] = {}
    asset_key_to_resource_props: Mapping[AssetKey, Mapping[str, Any]] = {}
    for assets_def in dbt_assets:
        manifest, translator = get_manifest_and_translator_from_dbt_assets([assets_def])
        asset_key_to_resource_props_for_def = get_asset_keys_to_resource_props(manifest, translator)
        for asset_key in asset_to_keys_iterable(assets_def):
            if asset_key not in asset_key_to_resource_props_for_def:
                raise DagsterInvariantViolationError(
                    f"Could not find dbt resource properties for asset key {asset_key.to_user_string()}."
                )
            asset_key_to_assets_def[asset_key] = assets_def
            asset_key_to_resource_props[asset_key] = asset_key_to_resource_props_for_def[asset_key]
    for asset_key in assets_to_keys(dbt_assets):
        dbt_resource_props = asset_key_to_resource_props[asset_key]
        assets_def = asset_key_to_assets_def[asset_key]
        dagster_metadata = dbt_resource_props.get("meta", {}).get("dagster", {})
        freshness_check_config = dagster_metadata.get("freshness_check", {})
        if not freshness_check_config:
            continue

        severity_str = freshness_check_config.get("severity")
        severity = AssetCheckSeverity(severity_str) if severity_str else DEFAULT_FRESHNESS_SEVERITY
        if assets_def.partitions_def and isinstance(
            assets_def.partitions_def, TimeWindowPartitionsDefinition
        ):
            freshness_checks.extend(
                build_time_partition_freshness_checks(
                    assets=[asset_key],
                    deadline_cron=freshness_check_config.get("deadline_cron"),
                    severity=severity,
                )
            )
        else:
            try:
                lower_bound_delta_seconds_str = freshness_check_config["lower_bound_delta_seconds"]
                lower_bound_seconds = int(lower_bound_delta_seconds_str)
            except:
                raise DagsterInvariantViolationError(
                    "lower_bound_delta_seconds must be provided, and parseable as an integer "
                    "in the freshness_check config for a non-time-partitioned asset."
                )

            freshness_checks.extend(
                build_last_update_freshness_checks(
                    assets=[translator.get_asset_key(dbt_resource_props)],  # pyright: ignore[reportPossiblyUnboundVariable]
                    deadline_cron=freshness_check_config.get("deadline_cron"),
                    lower_bound_delta=datetime.timedelta(seconds=lower_bound_seconds),
                    severity=severity,
                )
            )

    return freshness_checks
