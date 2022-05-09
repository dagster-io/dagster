from typing import Any, Optional

import dagster._check as check
from dagster.core.definitions.job_definition import JobDefinition
from dagster.core.definitions.logger_definition import LoggerDefinition
from dagster.core.definitions.pipeline_definition import PipelineDefinition
from dagster.core.errors import DagsterInvariantViolationError

from .output import RUN_ID_PLACEHOLDER


class InitLoggerContext:
    """Logger-specific initialization context.

    An instance of this class is made available as the first argument to the ``logger_fn`` decorated
    by :py:func:`@logger <logger>` or set on a :py:class:`LoggerDefinition`.

    Users should not instantiate this class.

    Attributes:
        logger_config (Any): The configuration data provided by the run config. The
            schema for this data is defined by ``config_schema`` on the :py:class:`LoggerDefinition`
        pipeline_def (Optional[PipelineDefinition]): The pipeline/job definition currently being executed.
        logger_def (Optional[LoggerDefinition]): The logger definition for the logger being constructed.
        run_id (str): The ID for this run of the pipeline.
    """

    def __init__(
        self,
        logger_config: Any,
        logger_def: Optional[LoggerDefinition] = None,
        pipeline_def: Optional[PipelineDefinition] = None,
        run_id: Optional[str] = None,
    ):
        self._logger_config = logger_config
        self._pipeline_def = check.opt_inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        self._logger_def = check.opt_inst_param(logger_def, "logger_def", LoggerDefinition)
        self._run_id = check.opt_str_param(run_id, "run_id")

    @property
    def logger_config(self) -> Any:
        return self._logger_config

    @property
    def pipeline_def(self) -> Optional[PipelineDefinition]:
        return self._pipeline_def

    @property
    def job_def(self) -> Optional[JobDefinition]:
        if not self._pipeline_def:
            return None
        if not isinstance(self._pipeline_def, JobDefinition):
            raise DagsterInvariantViolationError(
                "Attempted to access the .job_def property on an InitLoggerContext that was "
                "initialized with a PipelineDefinition. Please use .pipeline_def instead."
            )
        return self._pipeline_def

    @property
    def logger_def(self) -> Optional[LoggerDefinition]:
        return self._logger_def

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id


class UnboundInitLoggerContext(InitLoggerContext):
    """Logger initialization context outputted by ``build_init_logger_context``.

    Represents a context whose config has not yet been validated against a logger definition, hence
    the inability to access the `logger_def` attribute. When an instance of
    ``UnboundInitLoggerContext`` is passed to ``LoggerDefinition.initialize``, config is validated,
    and it is subsumed into an `InitLoggerContext`, which contains the logger_def validated against.
    """

    def __init__(self, logger_config: Any, pipeline_def: Optional[PipelineDefinition]):
        super(UnboundInitLoggerContext, self).__init__(
            logger_config, logger_def=None, pipeline_def=pipeline_def, run_id=None
        )

    @property
    def logger_def(self) -> LoggerDefinition:
        raise DagsterInvariantViolationError(
            "UnboundInitLoggerContext has not been validated against a logger definition."
        )

    @property
    def run_id(self) -> Optional[str]:
        return RUN_ID_PLACEHOLDER
