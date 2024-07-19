from typing import Any, Callable, Mapping, Optional, Set

from dagster import (
    AssetsDefinition,
    BackfillPolicy,
    PartitionsDefinition,
    RetryPolicy,
    TimeWindowPartitionsDefinition,
    multi_asset,
)

from .information_schema import SdfInformationSchema


def sdf_assets(
    *,
    information_schema: SdfInformationSchema,
    name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    required_resource_keys: Optional[Set[str]] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    outs, internal_asset_deps = information_schema.build_sdf_multi_asset_args(
        io_manager_key=io_manager_key
    )

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
        required_resource_keys=required_resource_keys,
        compute_kind="sdf",
        partitions_def=partitions_def,
        can_subset=True,
        op_tags=op_tags,
        backfill_policy=backfill_policy,
        retry_policy=retry_policy,
    )
