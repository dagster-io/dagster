from abc import ABC, abstractmethod, abstractproperty
from typing import Any, Optional

from dagster import check
from dagster.core.definitions.dependency import Solid
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.forked_pdb import ForkedPdb

from .step import StepExecutionContext
from .system import SystemComputeExecutionContext


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


class SolidExecutionContext(StepExecutionContext, AbstractComputeExecutionContext):
    """The ``context`` object available to solid compute logic."""

    __slots__ = ["_system_compute_execution_context"]

    def __init__(self, system_compute_execution_context: SystemComputeExecutionContext):
        self._system_compute_execution_context = check.inst_param(
            system_compute_execution_context,
            "system_compute_execution_context",
            SystemComputeExecutionContext,
        )
        self._pdb: Optional[ForkedPdb] = None
        super(SolidExecutionContext, self).__init__(system_compute_execution_context)

    @property
    def solid_config(self) -> Any:
        """The parsed config specific to this solid."""
        return self._system_compute_execution_context.solid_config

    @property
    def pipeline_run(self) -> PipelineRun:
        """The current PipelineRun"""
        return self._system_compute_execution_context.pipeline_run

    @property
    def instance(self) -> DagsterInstance:
        """The current Instance"""
        return self._system_compute_execution_context.instance

    @property
    def pdb(self) -> ForkedPdb:
        """Allows pdb debugging from within the solid.

        Example:

        .. code-block:: python

            @solid
            def debug_solid(context):
                context.pdb.set_trace()

        """
        if self._pdb is None:
            self._pdb = ForkedPdb()

        return self._pdb
