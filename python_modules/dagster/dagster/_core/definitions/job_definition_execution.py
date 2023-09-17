from typing import (
    AbstractSet,
    Iterable,
    Optional,
)

from dagster._core.definitions.asset_check_spec import AssetCheckHandle
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvariantViolationError

from .job_definition import UNEXECUTABLE_TAINT_PROPERTY, JobDefinition


# only this file is allowed to remove taint.
def _remove_unexecutable_taint(job_def: JobDefinition) -> JobDefinition:
    setattr(job_def, UNEXECUTABLE_TAINT_PROPERTY, False)
    return job_def


def job_has_unexecutable_taint(job_def: JobDefinition) -> bool:
    return getattr(job_def, UNEXECUTABLE_TAINT_PROPERTY)


# We have a "pattern" in the code base where in execution codepaths we generate
# job definition subsets in order to do runtime executition selection, e.g.
# the user provides an asset selection or an op selection at runtime. Unfortunately
# this is the same codepath that we use at *definition* time to construct job subsets
# using functions like "build_assets_job" which ends up calling "to_job" on
# a GraphDefinition. The get_subset function returns a vanilla job definition
# that has the type as the original, and no lineage. This is highly unfortuante.
# Without a single "choke point" for runtime subsetting, it is very easy to
# forget to call get_subset in production execution codepaths, and there is no
# single place to consolidate runtime subsetting execution logic.
#
# The execution taint is the first step in a plan to fix this. Job definitions
# will be tainted when they are first created. They are only untainted by calling
# create_untainted_job_for_execution. This function will remove the taint.
# We will insert invariants deep in the execution machinery to ensure that this
# is called in user space code before it is passed in for execution.
#
# When this process is complete, we could consider adding a different type to
# represent a chunk of a job to be executed, and remove the taint entirely, transferring
# that information from this dodgy monkeypatching to the type system. We can't
# do this in one go, so tainting it shall be.
#
# This function very deliberatately does not use default arguments. This is by
# design to that callers are forced to declare, in code, that they do not support
# our varietals of execution selection. There shall be no hiding your
# sins of call-stack-passing omissions and their resulting execution
# selection bugs from create_untainted_job_for_execution.
def create_untainted_job_for_execution(
    *,
    job_def: JobDefinition,
    op_selection: Optional[Iterable[str]],
    asset_selection: Optional[AbstractSet[AssetKey]],
    asset_check_selection: Optional[AbstractSet[AssetCheckHandle]],
):
    if asset_selection:
        for asset_key in asset_selection:
            if asset_key not in job_def.asset_layer.assets_defs_by_key:
                # disconnected asset key
                continue

            if not job_def.asset_layer.assets_defs_by_key[asset_key].is_asset_executable(asset_key):
                raise DagsterInvariantViolationError(
                    f'You have attempted to explicitly select asset "{asset_key.to_user_string()}"'
                    " for execution. This is not allowed as it is not executable."
                )

    return _remove_unexecutable_taint(
        job_def.get_subset(
            op_selection=op_selection,
            asset_selection=exclude_nonexecutables_from_selection(job_def, asset_selection),
            asset_check_selection=asset_check_selection,
        )
    )


def exclude_nonexecutables_from_selection(
    job_def: JobDefinition, asset_selection: Optional[AbstractSet[AssetKey]]
) -> Optional[AbstractSet[AssetKey]]:
    if asset_selection:
        return asset_selection

    nonexecutable_asset_list = []
    if job_def.asset_layer:
        for assets_def in job_def.asset_layer.assets_defs:
            if not assets_def.is_executable:
                nonexecutable_asset_list.extend(assets_def.keys)

        if nonexecutable_asset_list:
            asset_selection = set(job_def.asset_layer.asset_keys) - set(nonexecutable_asset_list)

    return asset_selection
