from typing import Any, Optional

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.errors import DagsterInvariantViolationError

from .output import RUN_ID_PLACEHOLDER


class InitLoggerContext:
    """The context object available as the argument to the initialization function of a :py:class:`dagster.LoggerDefinition`.

    Users should not instantiate this object directly. To construct an
    `InitLoggerContext` for testing purposes, use :py:func:`dagster.
    build_init_logger_context`.

    Example:
        .. code-block:: python

            from dagster import logger, InitLoggerContext

            @logger
            def hello_world(init_context: InitLoggerContext):
                ...

    """

    def __init__(
        self,
        logger_config: Any,
        logger_def: Optional[LoggerDefinition] = None,
        job_def: Optional[JobDefinition] = None,
        run_id: Optional[str] = None,
    ):
        self._logger_config = logger_config
        self._job_def = check.opt_inst_param(job_def, "job_def", JobDefinition)
        self._logger_def = check.opt_inst_param(logger_def, "logger_def", LoggerDefinition)
        self._run_id = check.opt_str_param(run_id, "run_id")

    @public
    @property
    def logger_config(self) -> Any:
        """The configuration data provided by the run config. The
        schema for this data is defined by ``config_schema`` on the :py:class:`LoggerDefinition`.
        """
        return self._logger_config

    @property
    def job_def(self) -> Optional[JobDefinition]:
        """The job definition currently being executed."""
        return self._job_def

    @public
    @property
    def logger_def(self) -> Optional[LoggerDefinition]:
        """The logger definition for the logger being constructed."""
        return self._logger_def

    @public
    @property
    def run_id(self) -> Optional[str]:
        """The ID for this run of the job."""
        return self._run_id


class UnboundInitLoggerContext(InitLoggerContext):
    """Logger initialization context outputted by ``build_init_logger_context``.

    Represents a context whose config has not yet been validated against a logger definition, hence
    the inability to access the `logger_def` attribute. When an instance of
    ``UnboundInitLoggerContext`` is passed to ``LoggerDefinition.initialize``, config is validated,
    and it is subsumed into an `InitLoggerContext`, which contains the logger_def validated against.
    """

    def __init__(self, logger_config: Any, job_def: Optional[JobDefinition]):
        super(UnboundInitLoggerContext, self).__init__(
            logger_config, logger_def=None, job_def=job_def, run_id=None
        )

    @property
    def logger_def(self) -> LoggerDefinition:
        raise DagsterInvariantViolationError(
            "UnboundInitLoggerContext has not been validated against a logger definition."
        )

    @property
    def run_id(self) -> Optional[str]:
        return RUN_ID_PLACEHOLDER
