import functools
import logging
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import ExitStack
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Union, cast, overload

from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.errors import DeserializationError
from dagster_shared.seven import JSONDecodeError
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import beta_param, deprecated_param, public
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.scoped_resources_builder import Resources, ScopedResourcesBuilder
from dagster._core.definitions.sensor_definition import (
    DagsterRunReaction,
    DefaultSensorStatus,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SensorResult,
    SensorReturnTypesUnion,
    SensorType,
    SkipReason,
    get_context_param_name,
    get_or_create_sensor_context,
    validate_and_get_resource_dict,
)
from dagster._core.definitions.target import ExecutableDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    RunStatusSensorExecutionError,
    user_code_error_boundary,
)
from dagster._core.event_api import RunStatusChangeEventType, RunStatusChangeRecordsFilter
from dagster._core.events import PIPELINE_RUN_STATUS_TO_EVENT_TYPE, DagsterEvent, DagsterEventType
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus, RunsFilter
from dagster._serdes import serialize_value, whitelist_for_serdes
from dagster._time import datetime_from_timestamp, parse_time_string
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.warnings import normalize_renamed_param

if TYPE_CHECKING:
    from datetime import datetime

    from dagster._core.definitions.resource_definition import ResourceDefinition
    from dagster._core.definitions.selector import (
        CodeLocationSelector,
        JobSelector,
        RepositorySelector,
    )

RunStatusSensorEvaluationFunction: TypeAlias = Union[
    Callable[..., SensorReturnTypesUnion],
    Callable[..., SensorReturnTypesUnion],
]
RunFailureSensorEvaluationFn: TypeAlias = Union[
    Callable[..., SensorReturnTypesUnion],
    Callable[..., SensorReturnTypesUnion],
]


def _get_run_status_sensor_fetch_limit(monitor_all_code_locations: bool) -> int:
    if monitor_all_code_locations:
        # No need to overfetch if we are going to process everything
        return _get_run_status_sensor_process_limit()

    # Otherwise, fetch more than we are planning to process, under the assumption
    # that some will be filtered out
    return int(os.getenv("DAGSTER_RUN_STATUS_SENSOR_FETCH_LIMIT", "25"))


def _get_run_status_sensor_process_limit() -> int:
    return int(os.getenv("DAGSTER_RUN_STATUS_SENSOR_PROCESS_LIMIT", "5"))


@whitelist_for_serdes(old_storage_names={"PipelineSensorCursor"})
class RunStatusSensorCursor(
    NamedTuple(
        "_RunStatusSensorCursor",
        [
            ("record_id", int),
            # deprecated arg, used as a record cursor for the run-sharded sqlite implementation to
            # filter records based on the update timestamp of the run.  When populated, the record
            # id is ignored (since it maybe run-scoped).
            ("update_timestamp", Optional[str]),
            # debug arg, used to quickly inspect the last processed timestamp from the run status
            # sensor's serialized state
            ("record_timestamp", Optional[str]),
        ],
    )
):
    def __new__(cls, record_id, update_timestamp=None, record_timestamp=None):
        return super().__new__(
            cls,
            record_id=check.int_param(record_id, "record_id"),
            update_timestamp=check.opt_str_param(update_timestamp, "update_timestamp"),
            record_timestamp=check.opt_str_param(record_timestamp, "record_timestamp"),
        )

    @staticmethod
    def is_valid(json_str: str) -> bool:
        try:
            obj = deserialize_value(json_str, RunStatusSensorCursor)
            return isinstance(obj, RunStatusSensorCursor)
        except (JSONDecodeError, DeserializationError):
            return False

    def to_json(self) -> str:
        return serialize_value(cast("NamedTuple", self))

    @staticmethod
    def from_json(json_str: str) -> "RunStatusSensorCursor":
        return deserialize_value(json_str, RunStatusSensorCursor)


@public
class RunStatusSensorContext:
    """The ``context`` object available to a decorated function of ``run_status_sensor``."""

    def __init__(
        self,
        sensor_name,
        dagster_run,
        dagster_event,
        instance,
        context: Optional[
            SensorEvaluationContext
        ] = None,  # deprecated arg, but we need to keep it for backcompat
        resource_defs: Optional[Mapping[str, "ResourceDefinition"]] = None,
        logger: Optional[logging.Logger] = None,
        partition_key: Optional[str] = None,
        repository_def: Optional[RepositoryDefinition] = None,
        _resources: Optional[Resources] = None,
        _cm_scope_entered: bool = False,
    ) -> None:
        self._exit_stack = ExitStack()
        self._sensor_name = check.str_param(sensor_name, "sensor_name")
        self._dagster_run = check.inst_param(dagster_run, "dagster_run", DagsterRun)
        self._dagster_event = check.inst_param(dagster_event, "dagster_event", DagsterEvent)
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._logger: Optional[logging.Logger] = logger or (context.log if context else None)
        self._partition_key = check.opt_str_param(partition_key, "partition_key")
        self._repository_def = check.opt_inst_param(
            repository_def, "repository_def", RepositoryDefinition
        )

        # Wait to set resources unless they're accessed
        self._resource_defs = resource_defs
        self._resources = _resources
        self._cm_scope_entered = _cm_scope_entered

    def for_run_failure(self) -> "RunFailureSensorContext":
        """Converts RunStatusSensorContext to RunFailureSensorContext."""
        return RunFailureSensorContext(
            sensor_name=self._sensor_name,
            dagster_run=self._dagster_run,
            dagster_event=self._dagster_event,
            instance=self._instance,
            logger=self._logger,
            partition_key=self._partition_key,
            resource_defs=self._resource_defs,
            repository_def=self._repository_def,
            _resources=self._resources,
            _cm_scope_entered=self._cm_scope_entered,
        )

    @property
    def resource_defs(self) -> Optional[Mapping[str, "ResourceDefinition"]]:
        return self._resource_defs

    @property
    def repository_def(self) -> Optional[RepositoryDefinition]:
        """Optional[RepositoryDefinition]: The RepositoryDefinition that this sensor resides in."""
        return self._repository_def

    @property
    def resources(self) -> Resources:
        from dagster._core.definitions.scoped_resources_builder import IContainsGenerator
        from dagster._core.execution.build_resources import build_resources

        if not self._resources:
            """
            This is similar to what we do in e.g. the op context - we set up a resource
            building context manager, and immediately enter it. This is so that in cases
            where a user is not using any context-manager based resources, they don't
            need to enter this SensorEvaluationContext themselves.

            For example:

            my_sensor(build_sensor_context(resources={"my_resource": my_non_cm_resource})

            will work ok, but for a CM resource we must do

            with build_sensor_context(resources={"my_resource": my_cm_resource}) as context:
                my_sensor(context)
            """

            instance = self.instance if self._instance else None

            resources_cm = build_resources(resources=self._resource_defs or {}, instance=instance)
            self._resources = self._exit_stack.enter_context(resources_cm)

            if isinstance(self._resources, IContainsGenerator) and not self._cm_scope_entered:
                self._exit_stack.close()
                raise DagsterInvariantViolationError(
                    "At least one provided resource is a generator, but attempting to access"
                    " resources outside of context manager scope. You can use the following syntax"
                    " to open a context manager: `with build_sensor_context(...) as context:`"
                )

        return self._resources

    @public
    @property
    def sensor_name(self) -> str:
        """The name of the sensor."""
        return self._sensor_name

    @public
    @property
    def dagster_run(self) -> DagsterRun:
        """The run of the job."""
        return self._dagster_run

    @public
    @property
    def dagster_event(self) -> DagsterEvent:
        """The event associated with the job run status."""
        return self._dagster_event

    @public
    @property
    def instance(self) -> DagsterInstance:
        """The current instance."""
        return self._instance

    @public
    @property
    def log(self) -> logging.Logger:
        """The logger for the current sensor evaluation."""
        if not self._logger:
            self._logger = InstigationLogger()

        return self._logger

    @public
    @property
    def partition_key(self) -> Optional[str]:
        """Optional[str]: The partition key of the relevant run."""
        return self._partition_key

    def __enter__(self) -> "RunStatusSensorContext":
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc) -> None:
        self._exit_stack.close()
        self._logger = None

    def merge_resources(self, resources_dict: Mapping[str, Any]) -> "RunStatusSensorContext":
        """Merge the specified resources into this context.

        This method is intended to be used by the Dagster framework, and should not be called by user code.

        Args:
            resources_dict (Mapping[str, Any]): The resources to replace in the context.
        """
        check.invariant(
            self._resources is None,
            "Cannot merge resources in context that has been initialized.",
        )
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        return RunStatusSensorContext(
            sensor_name=self._sensor_name,
            dagster_run=self._dagster_run,
            dagster_event=self._dagster_event,
            instance=self._instance,
            logger=self._logger,
            partition_key=self._partition_key,
            resource_defs={
                **(self._resource_defs or {}),
                **wrap_resources_for_execution(resources_dict),
            },
            repository_def=self._repository_def,
        )


@public
class RunFailureSensorContext(RunStatusSensorContext):
    """The ``context`` object available to a decorated function of ``run_failure_sensor``.

    Args:
        sensor_name (str): the name of the sensor.
        dagster_run (DagsterRun): the failed run.
    """

    @public
    @property
    def failure_event(self) -> DagsterEvent:
        """The run failure event.

        If the run failed because of an error inside a step, get_step_failure_events will have more
        details on the step failure.
        """
        return self.dagster_event

    @public
    def get_step_failure_events(self) -> Sequence[DagsterEvent]:
        """The step failure event for each step in the run that failed.

        Examples:
            .. code-block:: python

                error_strings_by_step_key = {
                    # includes the stack trace
                    event.step_key: event.event_specific_data.error.to_string()
                    for event in context.get_step_failure_events()
                }
        """
        records = self.instance.get_records_for_run(
            run_id=self.dagster_run.run_id, of_type=DagsterEventType.STEP_FAILURE
        ).records
        return [cast("DagsterEvent", record.event_log_entry.dagster_event) for record in records]


@public
@beta_param(param="repository_def")
def build_run_status_sensor_context(
    sensor_name: str,
    dagster_event: DagsterEvent,
    dagster_instance: DagsterInstance,
    dagster_run: DagsterRun,
    context: Optional[SensorEvaluationContext] = None,
    resources: Optional[Mapping[str, object]] = None,
    partition_key: Optional[str] = None,
    *,
    repository_def: Optional[RepositoryDefinition] = None,
) -> RunStatusSensorContext:
    """Builds run status sensor context from provided parameters.

    This function can be used to provide the context argument when directly invoking a function
    decorated with `@run_status_sensor` or `@run_failure_sensor`, such as when writing unit tests.

    Args:
        sensor_name (str): The name of the sensor the context is being constructed for.
        dagster_event (DagsterEvent): A DagsterEvent with the same event type as the one that
            triggers the run_status_sensor
        dagster_instance (DagsterInstance): The dagster instance configured for the context.
        dagster_run (DagsterRun): DagsterRun object from running a job
        resources (Optional[Mapping[str, object]]): A dictionary of resources to be made available
            to the sensor.
        repository_def (Optional[RepositoryDefinition]): The repository that the sensor belongs to.

    Examples:
        .. code-block:: python

            instance = DagsterInstance.ephemeral()
            result = my_job.execute_in_process(instance=instance)

            dagster_run = result.dagster_run
            dagster_event = result.get_job_success_event() # or get_job_failure_event()

            context = build_run_status_sensor_context(
                sensor_name="run_status_sensor_to_invoke",
                dagster_instance=instance,
                dagster_run=dagster_run,
                dagster_event=dagster_event,
            )
            run_status_sensor_to_invoke(context)
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    return RunStatusSensorContext(
        sensor_name=sensor_name,
        instance=dagster_instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
        resource_defs=wrap_resources_for_execution(resources),
        logger=context.log if context else None,
        partition_key=partition_key,
        repository_def=repository_def,
    )


@overload
def run_failure_sensor(
    name: RunFailureSensorEvaluationFn,
) -> SensorDefinition: ...


@overload
def run_failure_sensor(
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    monitor_all_code_locations: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_job: Optional[ExecutableDefinition] = None,
    request_jobs: Optional[Sequence[ExecutableDefinition]] = None,
    monitor_all_repositories: bool = False,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[RawMetadataMapping] = None,
) -> Callable[
    [RunFailureSensorEvaluationFn],
    SensorDefinition,
]: ...


@deprecated_param(
    param="job_selection",
    breaking_version="2.0",
    additional_warn_text="Use `monitored_jobs` instead.",
)
@public
@deprecated_param(
    param="monitor_all_repositories",
    breaking_version="2.0",
    additional_warn_text="Use `monitor_all_code_locations` instead.",
)
def run_failure_sensor(
    name: Optional[Union[RunFailureSensorEvaluationFn, str]] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    monitor_all_code_locations: Optional[bool] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_job: Optional[ExecutableDefinition] = None,
    request_jobs: Optional[Sequence[ExecutableDefinition]] = None,
    monitor_all_repositories: Optional[bool] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[RawMetadataMapping] = None,
) -> Union[
    SensorDefinition,
    Callable[
        [RunFailureSensorEvaluationFn],
        SensorDefinition,
    ],
]:
    """Creates a sensor that reacts to job failure events, where the decorated function will be
    run when a run fails.

    Takes a :py:class:`~dagster.RunFailureSensorContext`.

    Args:
        name (Optional[str]): The name of the job failure sensor. Defaults to the name of the
            decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, RepositorySelector, JobSelector, CodeLocationSelector]]]):
            The jobs in the current repository that will be monitored by this failure sensor.
            Defaults to None, which means the alert will be sent when any job in the current
            repository fails.
        monitor_all_code_locations (bool): If set to True, the sensor will monitor all runs in the
            Dagster deployment. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, RepositorySelector, JobSelector, CodeLocationSelector]]]):
            (deprecated in favor of monitored_jobs) The jobs in the current repository that will be
            monitored by this failure sensor. Defaults to None, which means the alert will be sent
            when any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJob]]): The job a RunRequest should
            execute if yielded from the sensor.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJob]]]):
            A list of jobs to be executed if RunRequests are yielded from the sensor.
        monitor_all_repositories (bool): (deprecated in favor of monitor_all_code_locations) If set to True,
            the sensor will monitor all runs in the Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.
    """

    def inner(
        fn: RunFailureSensorEvaluationFn,
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        jobs = monitored_jobs if monitored_jobs else job_selection
        monitor_all = normalize_renamed_param(
            monitor_all_code_locations,
            "monitor_all_code_locations",
            monitor_all_repositories,
            "monitor_all_repositories",
        )

        @run_status_sensor(
            run_status=DagsterRunStatus.FAILURE,
            name=sensor_name,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            monitored_jobs=jobs,
            monitor_all_code_locations=monitor_all,
            default_status=default_status,
            request_job=request_job,
            request_jobs=request_jobs,
            tags=tags,
            metadata=metadata,
        )
        @functools.wraps(fn)
        def _run_failure_sensor(*args, **kwargs) -> Any:
            args_modified = [
                arg.for_run_failure() if isinstance(arg, RunStatusSensorContext) else arg
                for arg in args
            ]
            kwargs_modified = {
                k: v.for_run_failure() if isinstance(v, RunStatusSensorContext) else v
                for k, v in kwargs.items()
            }
            return fn(*args_modified, **kwargs_modified)

        return _run_failure_sensor

    # This case is for when decorator is used bare, without arguments
    if callable(name):
        return inner(name)

    return inner


@public
class RunStatusSensorDefinition(SensorDefinition):
    """Define a sensor that reacts to a given status of job execution, where the decorated
    function will be evaluated when a run is at the given status.

    Args:
        name (str): The name of the sensor. Defaults to the name of the decorated function.
        run_status (DagsterRunStatus): The status of a run which will be
            monitored by the sensor.
        run_status_sensor_fn (Callable[[RunStatusSensorContext], Union[SkipReason, DagsterRunReaction]]): The core
            evaluation function for the sensor. Takes a :py:class:`~dagster.RunStatusSensorContext`.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, JobSelector, RepositorySelector, CodeLocationSelector]]]):
            The jobs in the current repository that will be monitored by this sensor. Defaults to
            None, which means the alert will be sent when any job in the repository fails.
        monitor_all_code_locations (bool): If set to True, the sensor will monitor all runs in the
            Dagster deployment. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition]]): The job a RunRequest should
            execute if yielded from the sensor.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]):
            A list of jobs to be executed if RunRequests are yielded from the sensor.
    """

    def __init__(
        self,
        name: str,
        run_status: DagsterRunStatus,
        run_status_sensor_fn: RunStatusSensorEvaluationFunction,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        monitored_jobs: Optional[
            Sequence[
                Union[
                    JobDefinition,
                    GraphDefinition,
                    UnresolvedAssetJobDefinition,
                    "RepositorySelector",
                    "JobSelector",
                    "CodeLocationSelector",
                ]
            ]
        ] = None,
        monitor_all_code_locations: Optional[bool] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        request_job: Optional[ExecutableDefinition] = None,
        request_jobs: Optional[Sequence[ExecutableDefinition]] = None,
        tags: Optional[Mapping[str, str]] = None,
        metadata: Optional[RawMetadataMapping] = None,
        required_resource_keys: Optional[set[str]] = None,
    ):
        from dagster._core.definitions.selector import (
            CodeLocationSelector,
            JobSelector,
            RepositorySelector,
        )

        check.str_param(name, "name")
        check.inst_param(run_status, "run_status", DagsterRunStatus)
        check.callable_param(run_status_sensor_fn, "run_status_sensor_fn")
        check.opt_int_param(minimum_interval_seconds, "minimum_interval_seconds")
        check.opt_str_param(description, "description")
        check.opt_list_param(
            monitored_jobs,
            "monitored_jobs",
            (
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                RepositorySelector,
                JobSelector,
                CodeLocationSelector,
            ),
        )
        check.inst_param(default_status, "default_status", DefaultSensorStatus)
        monitor_all_code_locations = check.opt_bool_param(
            monitor_all_code_locations, "monitor_all_code_locations", default=False
        )

        resource_arg_names: set[str] = {arg.name for arg in get_resource_args(run_status_sensor_fn)}

        combined_required_resource_keys = (
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            | resource_arg_names
        )

        # coerce CodeLocationSelectors to RepositorySelectors with repo name "__repository__"
        monitored_jobs = [
            job.to_repository_selector() if isinstance(job, CodeLocationSelector) else job
            for job in (monitored_jobs or [])
        ]

        self._run_status_sensor_fn = check.callable_param(
            run_status_sensor_fn, "run_status_sensor_fn"
        )
        event_type = PIPELINE_RUN_STATUS_TO_EVENT_TYPE[run_status]

        # split monitored_jobs into external repos, external jobs, and jobs in the current repo
        other_repos = (
            [x for x in monitored_jobs if isinstance(x, RepositorySelector)]
            if monitored_jobs
            else []
        )

        other_repo_jobs = (
            [x for x in monitored_jobs if isinstance(x, JobSelector)] if monitored_jobs else []
        )

        current_repo_jobs = (
            [x for x in monitored_jobs if not isinstance(x, (JobSelector, RepositorySelector))]
            if monitored_jobs
            else []
        )

        def _wrapped_fn(
            context: SensorEvaluationContext,
        ) -> Iterator[Union[RunRequest, SkipReason, DagsterRunReaction, SensorResult]]:
            # initiate the cursor to (most recent event id, current timestamp) when:
            # * it's the first time starting the sensor
            # * or, the cursor isn't in valid format (backcompt)
            if context.cursor is None or not RunStatusSensorCursor.is_valid(context.cursor):
                most_recent_event_records = context.instance.fetch_run_status_changes(
                    records_filter=event_type, limit=1
                ).records
                most_recent_event_id = (
                    most_recent_event_records[0].storage_id
                    if len(most_recent_event_records) == 1
                    else -1
                )
                record_timestamp = (
                    datetime_from_timestamp(most_recent_event_records[0].timestamp).isoformat()
                    if len(most_recent_event_records) == 1
                    else None
                )

                new_cursor = RunStatusSensorCursor(
                    record_id=most_recent_event_id, record_timestamp=record_timestamp
                )
                context.update_cursor(new_cursor.to_json())
                yield SkipReason(f"Initiating {name}. Set cursor to {new_cursor}")
                return

            sensor_cursor = RunStatusSensorCursor.from_json(context.cursor)

            process_limit = _get_run_status_sensor_process_limit()

            fetch_limit = _get_run_status_sensor_fetch_limit(
                monitor_all_code_locations=cast("bool", monitor_all_code_locations)
            )

            # Fetch events after the cursor id
            # * we move the cursor forward to the latest visited event's id to avoid revisits
            # * when the daemon is down, bc we persist the cursor info, we can go back to where we
            #   left and backfill alerts for the qualified events during the downtime
            if sensor_cursor.update_timestamp and context.instance.event_log_storage.is_run_sharded:
                # The run status sensor cursor has the timestamp set... and the event log storage
                # is run sharded.  We need to query the index shard by timestamp instead of by
                # record id (which is reindexed relative to some run sharded query).  When we update
                # the cursor, we should omit the timestamp, since this API only queries the global
                # index shard instead of the run shard.
                event_records = context.instance.fetch_run_status_changes(
                    records_filter=RunStatusChangeRecordsFilter(
                        event_type=cast("RunStatusChangeEventType", event_type),
                        after_timestamp=cast(
                            "datetime", parse_time_string(sensor_cursor.update_timestamp)
                        ).timestamp(),
                    ),
                    ascending=True,
                    limit=fetch_limit,
                ).records
            elif (
                context.instance.event_log_storage.supports_run_status_change_job_name_filter
                and monitored_jobs
                and all(
                    [
                        not isinstance(monitored, (RepositorySelector, CodeLocationSelector))
                        for monitored in monitored_jobs
                    ]
                )
            ):
                # the event log storage supports run status change selectors... we should construct
                # the appropriate job selectors so that we can filter the events by jobs in the
                # storage layer instead of in memory.  This should improve throughput since we will
                # avoid fetching events that we will filter out later on.
                job_names = _job_names_for_monitored(
                    cast(
                        "Sequence[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, JobSelector]]",
                        monitored_jobs,
                    )
                )
                event_records = context.instance.fetch_run_status_changes(
                    records_filter=RunStatusChangeRecordsFilter(
                        event_type=cast("RunStatusChangeEventType", event_type),
                        after_storage_id=sensor_cursor.record_id,
                        job_names=job_names,
                    ),
                    ascending=True,
                    limit=fetch_limit,
                ).records
            else:
                # the cursor storage id is globally unique, either because the event log storage is
                # not run sharded or because the cursor was set from an event returned from the
                # index shard. When we update the cursor, we should omit the timestamp, since this
                # API only queries the global index shard instead of the run shard.
                event_records = context.instance.fetch_run_status_changes(
                    records_filter=RunStatusChangeRecordsFilter(
                        event_type=cast("RunStatusChangeEventType", event_type),
                        after_storage_id=sensor_cursor.record_id,
                    ),
                    ascending=True,
                    limit=fetch_limit,
                ).records

            run_ids_to_fetch = list(
                set(event_record.event_log_entry.run_id for event_record in event_records)
            )

            run_records = (
                {
                    record.dagster_run.run_id: record
                    for record in context.instance.get_run_records(
                        filters=RunsFilter(run_ids=run_ids_to_fetch)
                    )
                }
                if run_ids_to_fetch
                else {}
            )

            num_processed_runs = 0
            for event_record in event_records:
                event_log_entry = event_record.event_log_entry
                storage_id = event_record.storage_id
                record_timestamp = datetime_from_timestamp(event_record.timestamp).isoformat()

                # skip if we couldn't find the right run
                if event_log_entry.run_id not in run_records:
                    context.update_cursor(
                        RunStatusSensorCursor(
                            record_id=storage_id, record_timestamp=record_timestamp
                        ).to_json()
                    )
                    continue

                dagster_run = run_records[event_log_entry.run_id].dagster_run
                job_match = False

                # if monitor_all_code_locations is provided, then we want to run the sensor for all jobs in all code locations
                if monitor_all_code_locations:
                    job_match = True

                sensor_location_name = (
                    context.code_location_origin.location_name
                    if context.code_location_origin
                    else None
                )
                sensor_repo_name = context.repository_name
                dagster_run_location_name = (
                    dagster_run.remote_job_origin.repository_origin.code_location_origin.location_name
                    if dagster_run.remote_job_origin
                    else None
                )
                dagster_run_repo_name = (
                    dagster_run.remote_job_origin.repository_origin.repository_name
                    if dagster_run.remote_job_origin
                    else None
                )

                # check if the run is in the current repository and (if provided) one of jobs specified in monitored_jobs
                # note: this also matches when both are None for testing uses cases
                if (
                    not job_match
                    and (sensor_location_name == dagster_run_location_name)
                    and (sensor_repo_name == dagster_run_repo_name)
                ):
                    if monitored_jobs:
                        if dagster_run.job_name in map(lambda x: x.name, current_repo_jobs):
                            job_match = True
                    else:
                        job_match = True

                if (
                    not job_match
                    and
                    # the job has a repository (not manually executed)
                    dagster_run.remote_job_origin
                ):
                    # check if the run is one of the jobs specified by JobSelector or RepositorySelector (ie in another repo)
                    # make a JobSelector for the run in question
                    remote_repository_origin = dagster_run.remote_job_origin.repository_origin
                    run_job_selector = JobSelector(
                        location_name=remote_repository_origin.code_location_origin.location_name,
                        repository_name=remote_repository_origin.repository_name,
                        job_name=dagster_run.job_name,
                    )
                    if run_job_selector in other_repo_jobs:
                        job_match = True

                    # make a RepositorySelector for the run in question
                    run_repo_selector = RepositorySelector(
                        location_name=remote_repository_origin.code_location_origin.location_name,
                        repository_name=remote_repository_origin.repository_name,
                    )
                    if run_repo_selector in other_repos:
                        job_match = True

                if not job_match:
                    # the run in question doesn't match any of the criteria for we advance the cursor and move on
                    context.update_cursor(
                        RunStatusSensorCursor(
                            record_id=storage_id, record_timestamp=record_timestamp
                        ).to_json()
                    )
                    continue

                # Stop processing runs once you reach a matching job but have exceeded the limit
                # (It's fine to keep advancing the cursor for runs that do not match)
                if num_processed_runs >= process_limit:
                    break

                num_processed_runs = num_processed_runs + 1

                serializable_error = None

                resource_args_populated = validate_and_get_resource_dict(
                    context.resources, name, resource_arg_names
                )

                try:
                    with (
                        RunStatusSensorContext(
                            sensor_name=name,
                            dagster_run=dagster_run,
                            dagster_event=event_log_entry.dagster_event,
                            instance=context.instance,
                            resource_defs=context.resource_defs,
                            logger=context.log,
                            partition_key=dagster_run.tags.get("dagster/partition"),
                            repository_def=context.repository_def,
                        ) as sensor_context,
                        user_code_error_boundary(
                            RunStatusSensorExecutionError,
                            lambda: f'Error occurred during the execution sensor "{name}".',
                        ),
                    ):
                        context_param_name = get_context_param_name(run_status_sensor_fn)
                        context_param = (
                            {context_param_name: sensor_context} if context_param_name else {}
                        )

                        sensor_return = run_status_sensor_fn(
                            **context_param,
                            **resource_args_populated,
                        )

                        if sensor_return is not None:
                            context.update_cursor(
                                RunStatusSensorCursor(
                                    record_id=storage_id,
                                    record_timestamp=record_timestamp,
                                ).to_json()
                            )

                            if isinstance(sensor_return, SensorResult):
                                if sensor_return.cursor:
                                    raise DagsterInvariantViolationError(
                                        f"Error in run status sensor {name}: Sensor returned a"
                                        " SensorResult with a cursor value. The cursor is managed"
                                        " by the sensor and should not be modified by a user."
                                    )
                                yield sensor_return
                            elif isinstance(
                                sensor_return,
                                (RunRequest, SkipReason, DagsterRunReaction),
                            ):
                                yield sensor_return
                            else:
                                yield from sensor_return
                            return
                except RunStatusSensorExecutionError as run_status_sensor_execution_error:
                    # When the user code errors, we report error to the sensor tick not the original run.
                    serializable_error = serializable_error_info_from_exc_info(
                        run_status_sensor_execution_error.original_exc_info
                    )

                context.update_cursor(
                    RunStatusSensorCursor(
                        record_id=storage_id, record_timestamp=record_timestamp
                    ).to_json()
                )

                # Yield DagsterRunReaction to indicate the execution success/failure.
                # The sensor machinery would
                # * report back to the original run if success
                # * update cursor and job state
                yield DagsterRunReaction(
                    dagster_run=dagster_run,
                    run_status=run_status,
                    error=serializable_error,
                )

        super().__init__(
            name=name,
            evaluation_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
            job=request_job,
            jobs=request_jobs,
            required_resource_keys=combined_required_resource_keys,
            tags=tags,
            metadata=metadata,
        )

    def __call__(self, *args, **kwargs) -> SensorReturnTypesUnion:
        context_param_name = get_context_param_name(self._run_status_sensor_fn)
        context = get_or_create_sensor_context(
            self._run_status_sensor_fn,
            *args,
            context_type=RunStatusSensorContext,
            **kwargs,
        )
        context_param = {context_param_name: context} if context_param_name and context else {}

        resources = validate_and_get_resource_dict(
            context.resources if context else ScopedResourcesBuilder.build_empty(),
            self._name,
            self._required_resource_keys,
        )
        return self._run_status_sensor_fn(**context_param, **resources)

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.RUN_STATUS


@deprecated_param(
    param="job_selection",
    breaking_version="2.0",
    additional_warn_text="Use `monitored_jobs` instead.",
)
@public
@deprecated_param(
    param="monitor_all_repositories",
    breaking_version="2.0",
    additional_warn_text="Use `monitor_all_code_locations` instead.",
)
def run_status_sensor(
    run_status: DagsterRunStatus,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                JobDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
                "CodeLocationSelector",
            ]
        ]
    ] = None,
    monitor_all_code_locations: Optional[bool] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_job: Optional[ExecutableDefinition] = None,
    request_jobs: Optional[Sequence[ExecutableDefinition]] = None,
    monitor_all_repositories: Optional[bool] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[RawMetadataMapping] = None,
) -> Callable[
    [RunStatusSensorEvaluationFunction],
    RunStatusSensorDefinition,
]:
    """Creates a sensor that reacts to a given status of job execution, where the decorated
    function will be run when a job is at the given status.

    Takes a :py:class:`~dagster.RunStatusSensorContext`.

    Args:
        run_status (DagsterRunStatus): The status of run execution which will be
            monitored by the sensor.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, RepositorySelector, JobSelector, CodeLocationSelector]]]):
            Jobs in the current code locations that will be monitored by this sensor. Defaults to None, which means the alert will
            be sent when any job in the code location matches the requested run_status. Jobs in external repositories can be monitored by using
            RepositorySelector or JobSelector.
        monitor_all_code_locations (Optional[bool]): If set to True, the sensor will monitor all runs in the Dagster deployment.
            If set to True, an error will be raised if you also specify monitored_jobs or job_selection.
            Defaults to False.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, RepositorySelector, JobSelector, CodeLocationSelector]]]):
            (deprecated in favor of monitored_jobs) Jobs in the current code location that will be
            monitored by this sensor. Defaults to None, which means the alert will be sent when
            any job in the code location matches the requested run_status.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The job that should be
            executed if a RunRequest is yielded from the sensor.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            A list of jobs to be executed if RunRequests are yielded from the sensor.
        monitor_all_repositories (Optional[bool]): (deprecated in favor of monitor_all_code_locations) If set to True, the sensor will monitor all runs in the Dagster instance.
            If set to True, an error will be raised if you also specify monitored_jobs or job_selection.
            Defaults to False.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.
    """

    def inner(
        fn: RunStatusSensorEvaluationFunction,
    ) -> RunStatusSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        jobs = monitored_jobs if monitored_jobs else job_selection
        monitor_all = normalize_renamed_param(
            monitor_all_code_locations,
            "monitor_all_code_locations",
            monitor_all_repositories,
            "monitor_all_repositories",
        )

        if jobs and monitor_all:
            raise DagsterInvalidDefinitionError(
                f"Cannot specify both {'monitor_all_code_locations' if monitor_all_code_locations else 'monitor_all_repositories'} and"
                f" {'monitored_jobs' if monitored_jobs else 'job_selection'}."
            )

        return RunStatusSensorDefinition(
            name=sensor_name,
            run_status=run_status,
            run_status_sensor_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            monitored_jobs=jobs,
            monitor_all_code_locations=monitor_all,
            default_status=default_status,
            request_job=request_job,
            request_jobs=request_jobs,
            tags=tags,
            metadata=metadata,
        )

    return inner


def _job_names_for_monitored(
    monitored: Sequence[
        Union[
            JobDefinition,
            GraphDefinition,
            UnresolvedAssetJobDefinition,
            "JobSelector",
        ]
    ],
) -> Sequence[str]:
    from dagster._core.definitions.selector import JobSelector

    job_names = []
    for m in monitored:
        if isinstance(m, JobSelector):
            job_names.append(m.job_name)
        else:
            job_names.append(m.name)
    return job_names
