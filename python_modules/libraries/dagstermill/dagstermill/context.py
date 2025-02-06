from collections.abc import Mapping
from typing import AbstractSet, Any, Optional, cast  # noqa: UP035

from dagster import (
    DagsterRun,
    JobDefinition,
    OpDefinition,
    _check as check,
)
from dagster._annotations import beta, public
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.execution.context.op_execution_context import AbstractComputeExecutionContext
from dagster._core.execution.context.system import PlanExecutionContext, StepExecutionContext
from dagster._core.log_manager import DagsterLogManager
from dagster._core.system_config.objects import ResolvedRunConfig


@beta
class DagstermillExecutionContext(AbstractComputeExecutionContext):
    """Dagstermill-specific execution context.

    Do not initialize directly: use :func:`dagstermill.get_context`.
    """

    def __init__(
        self,
        job_context: PlanExecutionContext,
        job_def: JobDefinition,
        resource_keys_to_init: AbstractSet[str],
        op_name: str,
        node_handle: NodeHandle,
        op_config: Any = None,
    ):
        self._job_context = check.inst_param(job_context, "job_context", PlanExecutionContext)
        self._job_def = check.inst_param(job_def, "job_def", JobDefinition)
        self._resource_keys_to_init = check.set_param(
            resource_keys_to_init, "resource_keys_to_init", of_type=str
        )
        self.op_name = check.str_param(op_name, "op_name")
        self.node_handle = check.inst_param(node_handle, "node_handle", NodeHandle)
        self._op_config = op_config

    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is defined on the context.

        Args:
            key (str): The key to check.

        Returns:
            bool
        """
        check.str_param(key, "key")
        return self._job_context.has_tag(key)

    def get_tag(self, key: str) -> Optional[str]:
        """Get a logging tag defined on the context.

        Args:
            key (str): The key to get.

        Returns:
            str
        """
        check.str_param(key, "key")
        return self._job_context.get_tag(key)

    @public
    @property
    def run_id(self) -> str:
        """str: The run_id for the context."""
        return self._job_context.run_id

    @public
    @property
    def run_config(self) -> Mapping[str, Any]:
        """dict: The run_config for the context."""
        return self._job_context.run_config

    @property
    def resolved_run_config(self) -> ResolvedRunConfig:
        """:class:`dagster.ResolvedRunConfig`: The resolved_run_config for the context."""
        return self._job_context.resolved_run_config

    @public
    @property
    def logging_tags(self) -> Mapping[str, str]:
        """dict: The logging tags for the context."""
        return self._job_context.logging_tags

    @public
    @property
    def job_name(self) -> str:
        """str: The name of the executing job."""
        return self._job_context.job_name

    @public
    @property
    def job_def(self) -> JobDefinition:
        """:class:`dagster.JobDefinition`: The job definition for the context.

        This will be a dagstermill-specific shim.
        """
        return self._job_def

    @property
    def repository_def(self) -> RepositoryDefinition:
        """:class:`dagster.RepositoryDefinition`: The repository definition for the context."""
        raise NotImplementedError

    @property
    def resources(self) -> Any:
        """collections.namedtuple: A dynamically-created type whose properties allow access to
        resources.
        """
        return self._job_context.scoped_resources_builder.build(
            required_resource_keys=self._resource_keys_to_init,
        )

    @public
    @property
    def run(self) -> DagsterRun:
        """:class:`dagster.DagsterRun`: The job run for the context."""
        return cast(DagsterRun, self._job_context.dagster_run)

    @property
    def log(self) -> DagsterLogManager:
        """:class:`dagster.DagsterLogManager`: The log manager for the context.

        Call, e.g., ``log.info()`` to log messages through the Dagster machinery.
        """
        return self._job_context.log

    @public
    @property
    def op_def(self) -> OpDefinition:
        """:class:`dagster.OpDefinition`: The op definition for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether an
        op definition was passed to ``dagstermill.get_context``.
        """
        return cast(OpDefinition, self._job_def.node_def_named(self.op_name))

    @property
    def node(self) -> Node:
        """:class:`dagster.Node`: The node for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether an
        op definition was passed to ``dagstermill.get_context``.
        """
        return self.job_def.get_node(self.node_handle)

    @public
    @property
    def op_config(self) -> Any:
        """collections.namedtuple: A dynamically-created type whose properties allow access to
        op-specific config.
        """
        if self._op_config:
            return self._op_config

        op_config = self.resolved_run_config.ops.get(self.op_name)
        return op_config.config if op_config else None


class DagstermillRuntimeExecutionContext(DagstermillExecutionContext):
    def __init__(
        self,
        job_context: PlanExecutionContext,
        job_def: JobDefinition,
        resource_keys_to_init: AbstractSet[str],
        op_name: str,
        step_context: StepExecutionContext,
        node_handle: NodeHandle,
        op_config: Any = None,
    ):
        self._step_context = check.inst_param(step_context, "step_context", StepExecutionContext)
        super().__init__(
            job_context,
            job_def,
            resource_keys_to_init,
            op_name,
            node_handle,
            op_config,
        )

    @property
    def step_context(self) -> StepExecutionContext:
        return self._step_context
