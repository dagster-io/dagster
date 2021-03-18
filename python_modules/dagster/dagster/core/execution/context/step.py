from typing import NamedTuple, Optional

from dagster import check
from dagster.core.definitions.dependency import Solid, SolidHandle
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.errors import DagsterInvalidPropertyError
from dagster.core.log_manager import DagsterLogManager

from .system import SystemStepExecutionContext


class StepExecutionContext:
    __slots__ = ["_system_step_execution_context"]

    def __init__(self, system_step_execution_context):
        self._system_step_execution_context = check.inst_param(
            system_step_execution_context,
            "system_step_execution_context",
            SystemStepExecutionContext,
        )

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
    def resources(self) -> NamedTuple:
        """NamedTuple: The currently available resources."""
        return self._system_step_execution_context.resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        """Optional[StepLauncher]: The current step launcher, if any."""
        return self._system_step_execution_context.step_launcher

    @property
    def run_id(self) -> str:
        """str: The id of the current execution's run."""
        return self._system_step_execution_context.run_id

    @property
    def run_config(self) -> dict:
        """dict: The run config for the current execution."""
        return self._system_step_execution_context.run_config

    @property
    def pipeline_def(self) -> PipelineDefinition:
        """PipelineDefinition: The currently executing pipeline."""
        return self._system_step_execution_context.pipeline_def

    @property
    def pipeline_name(self) -> str:
        """str: The name of the currently executing pipeline."""
        return self._system_step_execution_context.pipeline_name

    @property
    def mode_def(self) -> ModeDefinition:
        """ModeDefinition: The mode of the current execution."""
        return self._system_step_execution_context.mode_def

    @property
    def log(self) -> DagsterLogManager:
        """DagsterLogManager: The log manager available in the execution context."""
        return self._system_step_execution_context.log

    @property
    def solid_handle(self) -> SolidHandle:
        """SolidHandle: The current solid's handle.

        :meta private:
        """
        return self._system_step_execution_context.solid_handle

    @property
    def solid(self) -> Solid:
        """Solid: The current solid object.

        :meta private:

        """
        return self._system_step_execution_context.pipeline_def.get_solid(self.solid_handle)

    @property
    def solid_def(self) -> SolidDefinition:
        """SolidDefinition: The current solid definition."""
        return self._system_step_execution_context.pipeline_def.get_solid(
            self.solid_handle
        ).definition

    def has_tag(self, key: str) -> bool:
        """Check if a logging tag is set.

        Args:
            key (str): The tag to check.

        Returns:
            bool: Whether the tag is set.
        """
        return self._system_step_execution_context.has_tag(key)

    def get_tag(self, key: str) -> str:
        """Get a logging tag.

        Args:
            key (tag): The tag to get.

        Returns:
            str: The value of the tag.
        """
        return self._system_step_execution_context.get_tag(key)

    def get_system_context(self) -> SystemStepExecutionContext:
        """Allows advanced users (e.g. framework authors) to punch through to the underlying
        system context.

        :meta private:

        Returns:
            SystemStepExecutionContext: The underlying system context.
        """
        return self._system_step_execution_context
