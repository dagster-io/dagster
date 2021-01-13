from dagster import check
from dagster.core.errors import DagsterInvalidPropertyError

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
        raise DagsterInvalidPropertyError(
            "You have attempted to access the file manager which has been moved to resources in 0.10.0. "
            "Please access it via `context.resources.file_manager` instead."
        )

    @property
    def resources(self):
        return self._system_step_execution_context.resources

    @property
    def step_launcher(self):
        return self._system_step_execution_context.step_launcher

    @property
    def run_id(self):
        return self._system_step_execution_context.run_id

    @property
    def run_config(self):
        return self._system_step_execution_context.run_config

    @property
    def pipeline_def(self):
        return self._system_step_execution_context.pipeline_def

    @property
    def mode_def(self):
        return self._system_step_execution_context.mode_def

    @property
    def log(self):
        return self._system_step_execution_context.log

    @property
    def solid_handle(self):
        return self._system_step_execution_context.solid_handle

    @property
    def solid(self):
        return self._system_step_execution_context.pipeline_def.get_solid(self.solid_handle)

    @property
    def solid_def(self):
        return self._system_step_execution_context.pipeline_def.get_solid(
            self.solid_handle
        ).definition

    def has_tag(self, key):
        return self._system_step_execution_context.has_tag(key)

    def get_tag(self, key):
        return self._system_step_execution_context.get_tag(key)

    def get_system_context(self) -> SystemStepExecutionContext:
        """
        This allows advanced users (e.g. framework authors) to punch through
        to the underlying system context.
        """
        return self._system_step_execution_context
