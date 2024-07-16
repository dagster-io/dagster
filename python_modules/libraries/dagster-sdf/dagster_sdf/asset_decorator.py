from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Set, Union

from dagster import (
    AssetsDefinition,
    BackfillPolicy,
    PartitionsDefinition,
    RetryPolicy,
    TimeWindowPartitionsDefinition,
    multi_asset,
)

from .constants import DEFAULT_SDF_WORKSPACE_ENVIRONMENT
from .sdf_information_schema import SdfInformationSchema


def sdf_assets(
    *,
    workspace_dir: Union[Path, str],
    target_dir: Union[Path, str],
    environment: str = DEFAULT_SDF_WORKSPACE_ENVIRONMENT,
    name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    information_schema = SdfInformationSchema(
        workspace_dir=workspace_dir, target_dir=target_dir, environment=environment
    )
    outs, internal_asset_deps = information_schema.get_outs_and_internal_deps(
        io_manager_key=io_manager_key
    )

    resolved_op_tags = {
        **(op_tags if op_tags else {}),
    }

    if (
        partitions_def
        and isinstance(partitions_def, TimeWindowPartitionsDefinition)
        and not backfill_policy
    ):
        backfill_policy = BackfillPolicy.single_run()

    return multi_asset(
        outs=outs,
        name=name,
        internal_asset_deps=internal_asset_deps,
        deps=[],
        required_resource_keys=required_resource_keys,
        compute_kind="sdf",  # Purely cosmetic
        partitions_def=partitions_def,
        can_subset=True,
        op_tags=resolved_op_tags,
        check_specs=[],
        backfill_policy=backfill_policy,
        retry_policy=retry_policy,
    )
