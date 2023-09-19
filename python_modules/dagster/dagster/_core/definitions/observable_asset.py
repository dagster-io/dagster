# from typing import Sequence

# from dagster import _check as check
# from dagster._core.definitions.asset_spec import (
#     SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
#     AssetExecutionType,
#     AssetSpec,
# )
# from dagster._core.definitions.decorators.asset_decorator import asset, multi_asset
# from dagster._core.definitions.source_asset import (
#     SourceAsset,
#     wrap_source_asset_observe_fn_in_op_compute_fn,
# )
# from dagster._core.errors import DagsterInvariantViolationError
# from dagster._core.execution.context.compute import OpExecutionContext


# def create_unexecutable_observable_assets_def(specs: Sequence[AssetSpec]):
#     new_specs = []
#     for spec in specs:
#         check.invariant(
#             spec.auto_materialize_policy is None,
#             "auto_materialize_policy must be None since it is ignored",
#         )
#         check.invariant(spec.code_version is None, "code_version must be None since it is ignored")
#         check.invariant(
#             spec.freshness_policy is None, "freshness_policy must be None since it is ignored"
#         )
#         check.invariant(
#             spec.skippable is False,
#             "skippable must be False since it is ignored and False is the default",
#         )

#         new_specs.append(
#             AssetSpec(
#                 key=spec.key,
#                 description=spec.description,
#                 group_name=spec.group_name,
#                 metadata={
#                     **(spec.metadata or {}),
#                     **{
#                         SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE: (
#                             AssetExecutionType.UNEXECUTABLE.value
#                         )
#                     },
#                 },
#                 deps=spec.deps,
#             )
#         )

#     @multi_asset(specs=new_specs)
#     def an_asset() -> None:
#         raise DagsterInvariantViolationError(
#             f"You have attempted to execute an unexecutable asset {[spec.key for spec in specs]}"
#         )

#     return an_asset


# def create_assets_def_from_source_asset(source_asset: SourceAsset):
#     check.invariant(
#         source_asset.auto_observe_interval_minutes is None,
#         "Schedulable observable source assets not supported yet: auto_observe_interval_minutes"
#         " should be None",
#     )

#     injected_metadata = (
#         {SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE: AssetExecutionType.UNEXECUTABLE.value}
#         if source_asset.observe_fn is None
#         else {}
#     )

#     kwargs = {
#         "key": source_asset.key,
#         "metadata": {
#             **source_asset.metadata,
#             **injected_metadata,
#         },
#         "group_name": source_asset.group_name,
#         "description": source_asset.description,
#         "partitions_def": source_asset.partitions_def,
#     }

#     if source_asset.io_manager_def:
#         kwargs["io_manager_def"] = source_asset.io_manager_def
#     elif source_asset.io_manager_key:
#         kwargs["io_manager_key"] = source_asset.io_manager_key

#     kwargs["partitions_def"] = source_asset.partitions_def

#     if source_asset.observe_fn:
#         kwargs["resource_defs"] = source_asset.resource_defs

#     @asset(**kwargs)
#     def shim_asset(context: OpExecutionContext):
#         if not source_asset.observe_fn:
#             raise NotImplementedError(f"Asset {source_asset.key} is not executable")

#         op_function = wrap_source_asset_observe_fn_in_op_compute_fn(source_asset)
#         return_value = op_function.decorated_fn(context)
#         check.invariant(
#             return_value is None,
#             "The wrapped decorated_fn should return a value. If this changes, this code path must"
#             " changed to process the events appopriately.",
#         )

#     return shim_asset
