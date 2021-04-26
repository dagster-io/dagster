from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Optional

from dagster import check
from dagster.core.definitions.dependency import Solid, SolidHandle
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.resource import Resources
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.errors import DagsterInvalidPropertyError
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.forked_pdb import ForkedPdb

from .system import StepExecutionContext


class AbstractComputeExecutionContext(ABC):  # pylint: disable=no-init
    """Base class for solid context implemented by SolidExecutionContext and DagstermillExecutionContext"""

    @abstractmethod
    def has_tag(self, key) -> bool:
        """Implement this method to check if a logging tag is set."""

    @abstractmethod
    def get_tag(self, key: str) -> str:
        """Implement this method to get a logging tag."""

    @abstractproperty
    def run_id(self) -> str:
        """The run id for the context."""

    @abstractproperty
    def solid_def(self) -> SolidDefinition:
        """The solid definition corresponding to the execution step being executed."""

    @abstractproperty
    def solid(self) -> Solid:
        """The solid corresponding to the execution step being executed."""

    @abstractproperty
    def pipeline_def(self) -> PipelineDefinition:
        """The pipeline being executed."""

    @abstractproperty
    def pipeline_run(self) -> PipelineRun:
        """The PipelineRun object corresponding to the execution."""

    @abstractproperty
    def resources(self) -> Any:
        """Resources available in the execution context."""

    @abstractproperty
    def log(self) -> DagsterLogManager:
        """The log manager available in the execution context."""

    @abstractproperty
    def solid_config(self) -> Any:
        """The parsed config specific to this solid."""


class SolidExecutionContext(AbstractComputeExecutionContext):
    """The ``context`` object available as the first argument to every solid's compute function.

    Users should not instantiate this object directly.

    Example:

    .. code-block:: python

        @solid
        def hello_world(context: SolidExecutionContext):
            context.log.info("Hello, world!")

    """

    __slots__ = ["_step_execution_context"]

    def __init__(self, step_execution_context: StepExecutionContext):
        self._step_execution_context = check.inst_param(
            step_execution_context,
            "step_execution_context",
            StepExecutionContext,
        )
        self._pdb: Optional[ForkedPdb] = None

    @property
    def solid_config(self) -> Any:
        solid_config = self._step_execution_context.environment_config.solids.get(
            str(self.solid_handle)
        )
        return solid_config.config if solid_config else None

    @property
    def pipeline_run(self) -> PipelineRun:
        """PipelineRun: The current pipeline run"""
        return self._step_execution_context.pipeline_run

    @property
    def instance(self) -> DagsterInstance:
        """DagsterInstance: The current Dagster instance"""
        return self._step_execution_context.instance

    @property
    def pdb(self) -> ForkedPdb:
        """dagster.utils.forked_pdb.ForkedPdb: Gives access to pdb debugging from within the solid.

        Example:

        .. code-block:: python

            @solid
            def debug_solid(context):
                context.pdb.set_trace()

        """
        if self._pdb is None:
            self._pdb = ForkedPdb()

        return self._pdb

    @property
    def file_manager(self):
        """Deprecated access to the file manager.

        :meta private:
        """
        raise DagsterInvalidPropertyError(
            "You have attempted to access the file manager which has been moved to resources in 0.10.0. "
            "Please access it via `context.resources.file_manager` instead."
        )

    @property
    def resources(self) -> Resources:
        """Resources: The currently available resources."""
        return self._step_execution_context.resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        """Optional[StepLauncher]: The current step launcher, if any."""
        return self._step_execution_context.step_launcher

    @property
    def run_id(self) -> str:
        """str: The id of the current execution's run."""
        return self._step_execution_context.run_id

    @property
    def run_config(self) -> dict:
        """dict: The run config for the current execution."""
        return self._step_execution_context.run_config

    @property
    def pipeline_def(self) -> PipelineDefinition:
        """PipelineDefinition: The currently executing pipeline."""
        return self._step_execution_context.pipeline_def

    @property
    def pipeline_name(self) -> str:
        """str: The name of the currently executing pipeline."""
        return self._step_execution_context.pipeline_name

    @property
    def mode_def(self) -> ModeDefinition:
        """ModeDefinition: The mode of the current execution."""
        return self._step_execution_context.mode_def

    @property
    def log(self) -> DagsterLogManager:
        """DagsterLogManager: The log manager available in the execution context."""
        return self._step_execution_context.log

    @property
    def solid_handle(self) -> SolidHandle:
        """SolidHandle: The current solid's handle.

        :meta private:
        """
        return self._step_execution_context.solid_handle

    @property
    def solid(self) -> Solid:
        """Solid: The current solid object.

        :meta private:

        """
        return self._step_execution_context.pipeline_def.get_solid(self.solid_handle)

    @property
    def solid_def(self) -> SolidDefinition:
        """SolidDefinition: The current solid definition."""
        return self._step_execution_context.pipeline_def.get_solid(self.solid_handle).definition

    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is set.

        Args:
            key (str): The tag to check.

        Returns:
            bool: Whether the tag is set.
        """
        return self._step_execution_context.has_tag(key)

    def get_tag(self, key: str) -> str:
        """Get a logging tag.

        Args:
            key (tag): The tag to get.

        Returns:
            str: The value of the tag.
        """
        return self._step_execution_context.get_tag(key)

    def get_step_execution_context(self) -> StepExecutionContext:
        """Allows advanced users (e.g. framework authors) to punch through to the underlying
        step execution context.

        :meta private:

        Returns:
            StepExecutionContext: The underlying system context.
        """
        return self._step_execution_context
