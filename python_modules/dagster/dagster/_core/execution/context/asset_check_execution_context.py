from collections.abc import Sequence
from typing import AbstractSet, Any, Optional  # noqa: UP035

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.asset_execution_context import (
    _copy_docs_from_op_execution_context,
)
from dagster._core.execution.context.op_execution_context import OpExecutionContext
from dagster._core.execution.context.system import StepExecutionContext
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.dagster_run import DagsterRun
from dagster._utils.forked_pdb import ForkedPdb


@public
class AssetCheckExecutionContext:
    def __init__(self, op_execution_context: OpExecutionContext) -> None:
        self._op_execution_context = check.inst_param(
            op_execution_context, "op_execution_context", OpExecutionContext
        )
        self._step_execution_context = self._op_execution_context._step_execution_context  # noqa: SLF001

    @staticmethod
    def get() -> "AssetCheckExecutionContext":
        from dagster._core.execution.context.compute import current_execution_context

        ctx = current_execution_context.get()
        if ctx is None:
            raise DagsterInvariantViolationError("No current AssetExecutionContext in scope.")
        if not isinstance(ctx, AssetCheckExecutionContext):
            raise DagsterInvariantViolationError(
                "Can't use AssetCheckExecutionContext.get() in the context of an "
                "AssetCheckExecutionContext or OpExecutionContext. Use AssetCheckExecutionContext.get() instead."
            )
        return ctx

    @property
    def op_execution_context(self) -> OpExecutionContext:
        return self._op_execution_context

    @public
    @property
    def log(self) -> DagsterLogManager:
        """The log manager available in the execution context. Logs will be viewable in the Dagster UI.
        Returns: DagsterLogManager.
        """
        return self.op_execution_context.log

    @public
    @property
    def pdb(self) -> ForkedPdb:
        """Gives access to pdb debugging from within the asset. Materializing the asset via the
        Dagster UI or CLI will enter the pdb debugging context in the process used to launch the UI or
        run the CLI.

        Returns: dagster.utils.forked_pdb.ForkedPdb
        """
        return self.op_execution_context.pdb

    @property
    def run(self) -> DagsterRun:
        """The DagsterRun object corresponding to the execution. Information like run_id,
        run configuration, and the assets selected for materialization can be found on the DagsterRun.
        """
        return self.op_execution_context.run

    @public
    @property
    def job_def(self) -> JobDefinition:
        """The definition for the currently executing job. Information like the job name, and job tags
        can be found on the JobDefinition.
        Returns: JobDefinition.
        """
        return self.op_execution_context.job_def

    @property
    def repository_def(self) -> RepositoryDefinition:
        """RepositoryDefinition: The Dagster repository for the currently executing job."""
        return self.op_execution_context.repository_def

    #### check related
    @public
    @property
    @_copy_docs_from_op_execution_context
    def selected_asset_check_keys(self) -> AbstractSet[AssetCheckKey]:
        return self.op_execution_context.selected_asset_check_keys

    @public
    @property
    def check_specs(self) -> Sequence[AssetCheckSpec]:
        """The asset check specs for the currently executing asset check."""
        return list(self.op_execution_context.assets_def.check_specs)

    #### op related

    @property
    @_copy_docs_from_op_execution_context
    def retry_number(self):
        return self.op_execution_context.retry_number

    @_copy_docs_from_op_execution_context
    def describe_op(self) -> str:
        return self.op_execution_context.describe_op()

    @public
    @property
    @_copy_docs_from_op_execution_context
    def op_def(self) -> OpDefinition:
        return self.op_execution_context.op_def

    #### execution related

    @public
    @property
    @_copy_docs_from_op_execution_context
    def instance(self) -> DagsterInstance:
        return self.op_execution_context.instance

    @property
    @_copy_docs_from_op_execution_context
    def step_launcher(self) -> Optional[StepLauncher]:
        return self.op_execution_context.step_launcher

    @_copy_docs_from_op_execution_context
    def get_step_execution_context(self) -> StepExecutionContext:
        return self.op_execution_context.get_step_execution_context()

    # misc

    @public
    @property
    @_copy_docs_from_op_execution_context
    def resources(self) -> Any:
        return self.op_execution_context.resources

    @property
    @_copy_docs_from_op_execution_context
    def is_subset(self):
        return self.op_execution_context.is_subset
