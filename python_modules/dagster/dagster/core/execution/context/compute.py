from abc import ABC, abstractmethod, abstractproperty
from typing import Any

from dagster import check
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.utils.forked_pdb import ForkedPdb

from .step import StepExecutionContext
from .system import SystemComputeExecutionContext


class AbstractComputeExecutionContext(ABC):  # pylint: disable=no-init
    """Base class for solid context implemented by SolidExecutionContext and DagstermillExecutionContext"""

    @abstractmethod
    def has_tag(self, key):
        """Implement this method to check if a logging tag is set."""

    @abstractmethod
    def get_tag(self, key):
        """Implement this method to get a logging tag."""

    @abstractproperty
    def run_id(self):
        """The run id for the context."""

    @abstractproperty
    def solid_def(self):
        """The solid definition corresponding to the execution step being executed."""

    @abstractproperty
    def solid(self):
        """The solid corresponding to the execution step being executed."""

    @abstractproperty
    def pipeline_def(self):
        """The pipeline being executed."""

    @abstractproperty
    def pipeline_run(self) -> PipelineRun:
        """The PipelineRun object corresponding to the execution."""

    @abstractproperty
    def resources(self) -> Any:
        """Resources available in the execution context."""

    @abstractproperty
    def log(self):
        """The log manager available in the execution context."""

    @abstractproperty
    def solid_config(self):
        """The parsed config specific to this solid."""


class SolidExecutionContext(StepExecutionContext, AbstractComputeExecutionContext):
    """The ``context`` object available to solid compute logic."""

    __slots__ = ["_system_compute_execution_context"]

    def __init__(self, system_compute_execution_context):
        self._system_compute_execution_context = check.inst_param(
            system_compute_execution_context,
            "system_compute_execution_context",
            SystemComputeExecutionContext,
        )
        self._pdb = None
        super(SolidExecutionContext, self).__init__(system_compute_execution_context)

    @property
    def solid_config(self):
        """The parsed config specific to this solid."""
        return self._system_compute_execution_context.solid_config

    @property
    def pipeline_run(self):
        """The current PipelineRun"""
        return self._system_compute_execution_context.pipeline_run

    @property
    def instance(self):
        """The current Instance"""
        return self._system_compute_execution_context.instance

    @property
    def pdb(self):
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
