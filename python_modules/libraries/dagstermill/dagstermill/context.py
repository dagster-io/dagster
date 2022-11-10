from typing import AbstractSet, Any, Mapping, Optional, cast

from dagster import DagsterRun, JobDefinition, OpDefinition
from dagster import _check as check
from dagster._annotations import public
from dagster._core.definitions.dependency import Node, NodeHandle
from dagster._core.execution.context.compute import AbstractComputeExecutionContext
from dagster._core.execution.context.system import PlanExecutionContext, StepExecutionContext
from dagster._core.log_manager import DagsterLogManager
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._legacy import PipelineDefinition, PipelineRun, SolidDefinition
from dagster._utils.backcompat import deprecation_warning


class DagstermillExecutionContext(AbstractComputeExecutionContext):
    """Dagstermill-specific execution context.

    Do not initialize directly: use :func:`dagstermill.get_context`.
    """

    def __init__(
        self,
        pipeline_context: PlanExecutionContext,
        pipeline_def: PipelineDefinition,
        resource_keys_to_init: AbstractSet[str],
        solid_name: str,
        solid_handle: NodeHandle,
        solid_config: Any = None,
    ):
        self._pipeline_context = check.inst_param(
            pipeline_context, "pipeline_context", PlanExecutionContext
        )
        self._pipeline_def = check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        self._resource_keys_to_init = check.set_param(
            resource_keys_to_init, "resource_keys_to_init", of_type=str
        )
        self.solid_name = check.str_param(solid_name, "solid_name")
        self.solid_handle = check.inst_param(solid_handle, "solid_handle", NodeHandle)
        self._solid_config = solid_config

    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is defined on the context.

        Args:
            key (str): The key to check.

        Returns:
            bool
        """
        check.str_param(key, "key")
        return self._pipeline_context.has_tag(key)

    def get_tag(self, key: str) -> Optional[str]:
        """Get a logging tag defined on the context.

        Args:
            key (str): The key to get.

        Returns:
            str
        """
        check.str_param(key, "key")
        return self._pipeline_context.get_tag(key)

    @public  # type: ignore
    @property
    def run_id(self) -> str:
        """str: The run_id for the context."""
        return self._pipeline_context.run_id

    @public  # type: ignore
    @property
    def run_config(self) -> Mapping[str, Any]:
        """dict: The run_config for the context."""
        return self._pipeline_context.run_config

    @property
    def resolved_run_config(self) -> ResolvedRunConfig:
        """:class:`dagster.ResolvedRunConfig`: The resolved_run_config for the context"""
        return self._pipeline_context.resolved_run_config

    @public  # type: ignore
    @property
    def logging_tags(self) -> Mapping[str, str]:
        """dict: The logging tags for the context."""
        return self._pipeline_context.logging_tags

    @public  # type: ignore
    @property
    def job_name(self) -> str:
        return self._pipeline_context.job_name

    @property
    def pipeline_name(self) -> str:
        deprecation_warning(
            "DagstermillExecutionContext.pipeline_name",
            "0.17.0",
            "use the 'job_name' property instead.",
        )
        return self.job_name

    @public  # type: ignore
    @property
    def job_def(self) -> JobDefinition:
        """:class:`dagster.JobDefinition`: The job definition for the context.

        This will be a dagstermill-specific shim.
        """
        return cast(
            JobDefinition,
            check.inst(
                self._pipeline_def,
                JobDefinition,
                "Accessing job_def inside a legacy pipeline. Use pipeline_def instead.",
            ),
        )

    @property
    def pipeline_def(self) -> PipelineDefinition:
        """:class:`dagster.PipelineDefinition`: The pipeline definition for the context.

        This will be a dagstermill-specific shim.
        """
        deprecation_warning(
            "DagstermillExecutionContext.pipeline_def",
            "0.17.0",
            "use the 'job_def' property instead.",
        )
        return self._pipeline_def

    @property
    def resources(self) -> Any:
        """collections.namedtuple: A dynamically-created type whose properties allow access to
        resources."""
        return self._pipeline_context.scoped_resources_builder.build(
            required_resource_keys=self._resource_keys_to_init,
        )

    @public  # type: ignore
    @property
    def run(self) -> DagsterRun:
        """:class:`dagster.DagsterRun`: The job run for the context."""
        return cast(DagsterRun, self._pipeline_context.pipeline_run)

    @property
    def pipeline_run(self) -> PipelineRun:
        deprecation_warning(
            "DagstermillExecutionContext.pipeline_run",
            "0.17.0",
            "use the 'run' property instead.",
        )
        return self.run

    @property
    def log(self) -> DagsterLogManager:
        """:class:`dagster.DagsterLogManager`: The log manager for the context.

        Call, e.g., ``log.info()`` to log messages through the Dagster machinery.
        """
        return self._pipeline_context.log

    @public  # type: ignore
    @property
    def op_def(self) -> OpDefinition:
        """:class:`dagster.OpDefinition`: The op definition for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether an
        op definition was passed to ``dagstermill.get_context``.
        """
        return cast(OpDefinition, self._pipeline_def.solid_def_named(self.solid_name))

    @property
    def solid_def(self) -> SolidDefinition:
        """:class:`dagster.SolidDefinition`: The solid definition for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether a
        solid definition was passed to ``dagstermill.get_context``.
        """
        deprecation_warning(
            "DagstermillExecutionContext.solid_def",
            "0.17.0",
            "use the 'op_def' property instead.",
        )
        return cast(SolidDefinition, self._pipeline_def.solid_def_named(self.solid_name))

    @property
    def solid(self) -> Node:
        """:class:`dagster.Node`: The solid for the context.

        In interactive contexts, this may be a dagstermill-specific shim, depending whether a
        solid definition was passed to ``dagstermill.get_context``.
        """
        deprecation_warning(
            "DagstermillExecutionContext.solid_def",
            "0.17.0",
            "use the 'op_def' property instead.",
        )
        return self.pipeline_def.get_solid(self.solid_handle)

    @public  # type: ignore
    @property
    def op_config(self) -> Any:
        """collections.namedtuple: A dynamically-created type whose properties allow access to
        op-specific config."""
        if self._solid_config:
            return self._solid_config

        solid_config = self.resolved_run_config.solids.get(self.solid_name)
        return solid_config.config if solid_config else None

    @property
    def solid_config(self) -> Any:
        """collections.namedtuple: A dynamically-created type whose properties allow access to
        solid-specific config."""
        deprecation_warning(
            "DagstermillExecutionContext.solid_config",
            "0.17.0",
            "use the 'op_config' property instead.",
        )
        return self.op_config


class DagstermillRuntimeExecutionContext(DagstermillExecutionContext):
    def __init__(
        self,
        pipeline_context: PlanExecutionContext,
        pipeline_def: PipelineDefinition,
        resource_keys_to_init: AbstractSet[str],
        solid_name: str,
        step_context: StepExecutionContext,
        solid_handle: NodeHandle,
        solid_config: Any = None,
    ):
        self._step_context = check.inst_param(step_context, "step_context", StepExecutionContext)
        super().__init__(
            pipeline_context,
            pipeline_def,
            resource_keys_to_init,
            solid_name,
            solid_handle,
            solid_config,
        )
