import inspect
import logging
from collections import defaultdict
from contextlib import ExitStack
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import pendulum
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.definitions.partition import (
    CachingDynamicPartitionsLoader,
)
from dagster._core.definitions.resource_annotation import (
    get_resource_args,
)
from dagster._core.definitions.resource_definition import (
    Resources,
)
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._serdes import whitelist_for_serdes
from dagster._utils import IHasInternalInit, normalize_to_repository

from ..decorator_utils import (
    get_function_params,
)
from .asset_selection import AssetSelection
from .graph_definition import GraphDefinition
from .job_definition import JobDefinition
from .run_request import (
    AddDynamicPartitionsRequest,
    DagsterRunReaction,
    DeleteDynamicPartitionsRequest,
    RunRequest,
    SensorResult,
    SkipReason,
)
from .target import DirectTarget, ExecutableDefinition, RepoRelativeTarget
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster import ResourceDefinition
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.repository_definition import RepositoryDefinition


@whitelist_for_serdes
class DefaultSensorStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


@whitelist_for_serdes
class SensorType(Enum):
    STANDARD = "STANDARD"
    RUN_STATUS = "RUN_STATUS"
    ASSET = "ASSET"
    MULTI_ASSET = "MULTI_ASSET"
    FRESHNESS_POLICY = "FRESHNESS_POLICY"
    UNKNOWN = "UNKNOWN"


DEFAULT_SENSOR_DAEMON_INTERVAL = 30


class SensorEvaluationContext:
    """The context object available as the argument to the evaluation function of a :py:class:`dagster.SensorDefinition`.

    Users should not instantiate this object directly. To construct a
    `SensorEvaluationContext` for testing purposes, use :py:func:`dagster.
    build_sensor_context`.

    Attributes:
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        cursor (Optional[str]): The cursor, passed back from the last sensor evaluation via
            the cursor attribute of SkipReason and RunRequest
        last_completion_time (float): DEPRECATED The last time that the sensor was evaluated (UTC).
        last_run_key (str): DEPRECATED The run key of the RunRequest most recently created by this
            sensor. Use the preferred `cursor` attribute instead.
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.
        repository_def (Optional[RepositoryDefinition]): The repository or that
            the sensor belongs to. If needed by the sensor top-level resource definitions will be
            pulled from this repository. You can provide either this or `definitions`.
        instance (Optional[DagsterInstance]): The deserialized instance can also be passed in
            directly (primarily useful in testing contexts).
        definitions (Optional[Definitions]): `Definitions` object that the sensor is defined in.
            If needed by the sensor, top-level resource definitions will be pulled from these
            definitions. You can provide either this or `repository_def`.
        resources (Optional[Dict[str, Any]]): A dict of resource keys to resource
            definitions to be made available during sensor execution.

    Example:
        .. code-block:: python

            from dagster import sensor, SensorEvaluationContext

            @sensor
            def the_sensor(context: SensorEvaluationContext):
                ...

    """

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        repository_name: Optional[str],
        repository_def: Optional["RepositoryDefinition"] = None,
        instance: Optional[DagsterInstance] = None,
        sensor_name: Optional[str] = None,
        resources: Optional[Mapping[str, "ResourceDefinition"]] = None,
        definitions: Optional["Definitions"] = None,
    ):
        from dagster._core.definitions.definitions_class import Definitions
        from dagster._core.definitions.repository_definition import RepositoryDefinition

        self._exit_stack = ExitStack()
        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )
        self._last_run_key = check.opt_str_param(last_run_key, "last_run_key")
        self._cursor = check.opt_str_param(cursor, "cursor")
        self._repository_name = check.opt_str_param(repository_name, "repository_name")
        self._repository_def = normalize_to_repository(
            check.opt_inst_param(definitions, "definitions", Definitions),
            check.opt_inst_param(repository_def, "repository_def", RepositoryDefinition),
            error_on_none=False,
        )
        self._instance = check.opt_inst_param(instance, "instance", DagsterInstance)
        self._sensor_name = sensor_name

        # Wait to set resources unless they're accessed
        self._resource_defs = resources
        self._resources = None
        self._cm_scope_entered = False

        self._log_key = (
            [
                repository_name,
                sensor_name,
                pendulum.now("UTC").strftime("%Y%m%d_%H%M%S"),
            ]
            if repository_name and sensor_name
            else None
        )
        self._logger: Optional[InstigationLogger] = None
        self._cursor_updated = False

    def __enter__(self) -> "SensorEvaluationContext":
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc) -> None:
        self._exit_stack.close()
        self._logger = None

    @property
    def resource_defs(self) -> Optional[Mapping[str, "ResourceDefinition"]]:
        return self._resource_defs

    def merge_resources(self, resources_dict: Mapping[str, Any]) -> "SensorEvaluationContext":
        """Merge the specified resources into this context.

        This method is intended to be used by the Dagster framework, and should not be called by user code.

        Args:
            resources_dict (Mapping[str, Any]): The resources to replace in the context.
        """
        check.invariant(
            self._resources is None, "Cannot merge resources in context that has been initialized."
        )
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        return SensorEvaluationContext(
            instance_ref=self._instance_ref,
            last_completion_time=self._last_completion_time,
            last_run_key=self._last_run_key,
            cursor=self._cursor,
            repository_name=self._repository_name,
            repository_def=self._repository_def,
            instance=self._instance,
            sensor_name=self._sensor_name,
            resources={
                **(self._resource_defs or {}),
                **wrap_resources_for_execution(resources_dict),
            },
        )

    @public
    @property
    def resources(self) -> Resources:
        from dagster._core.definitions.scoped_resources_builder import (
            IContainsGenerator,
        )
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

            instance = self.instance if self._instance or self._instance_ref else None

            resources_cm = build_resources(resources=self._resource_defs or {}, instance=instance)
            self._resources = self._exit_stack.enter_context(resources_cm)

            if isinstance(self._resources, IContainsGenerator) and not self._cm_scope_entered:
                self._exit_stack.close()
                raise DagsterInvariantViolationError(
                    "At least one provided resource is a generator, but attempting to access"
                    " resources outside of context manager scope. You can use the following syntax"
                    " to open a context manager: `with build_schedule_context(...) as context:`"
                )

        return self._resources

    @public
    @property
    def instance(self) -> DagsterInstance:
        # self._instance_ref should only ever be None when this SensorEvaluationContext was
        # constructed under test.
        if not self._instance:
            if not self._instance_ref:
                raise DagsterInvariantViolationError(
                    "Attempted to initialize dagster instance, but no instance reference was"
                    " provided."
                )
            self._instance = self._exit_stack.enter_context(
                DagsterInstance.from_ref(self._instance_ref)
            )
        return cast(DagsterInstance, self._instance)

    @property
    def instance_ref(self) -> Optional[InstanceRef]:
        return self._instance_ref

    @public
    @property
    def last_completion_time(self) -> Optional[float]:
        return self._last_completion_time

    @public
    @property
    def last_run_key(self) -> Optional[str]:
        return self._last_run_key

    @public
    @property
    def cursor(self) -> Optional[str]:
        """The cursor value for this sensor, which was set in an earlier sensor evaluation."""
        return self._cursor

    @public
    def update_cursor(self, cursor: Optional[str]) -> None:
        """Updates the cursor value for this sensor, which will be provided on the context for the
        next sensor evaluation.

        This can be used to keep track of progress and avoid duplicate work across sensor
        evaluations.

        Args:
            cursor (Optional[str]):
        """
        self._cursor = check.opt_str_param(cursor, "cursor")
        self._cursor_updated = True

    @property
    def cursor_updated(self) -> bool:
        return self._cursor_updated

    @public
    @property
    def repository_name(self) -> Optional[str]:
        return self._repository_name

    @public
    @property
    def repository_def(self) -> Optional["RepositoryDefinition"]:
        return self._repository_def

    @property
    def log(self) -> logging.Logger:
        if self._logger:
            return self._logger

        if not self._instance_ref:
            self._logger = self._exit_stack.enter_context(
                InstigationLogger(
                    self._log_key,
                    repository_name=self._repository_name,
                    name=self._sensor_name,
                )
            )
            return cast(logging.Logger, self._logger)

        self._logger = self._exit_stack.enter_context(
            InstigationLogger(
                self._log_key,
                self.instance,
                repository_name=self._repository_name,
                name=self._sensor_name,
            )
        )
        return cast(logging.Logger, self._logger)

    def has_captured_logs(self):
        return self._logger and self._logger.has_captured_logs()

    @property
    def log_key(self) -> Optional[List[str]]:
        return self._log_key


RawSensorEvaluationFunctionReturn = Union[
    Iterator[Union[SkipReason, RunRequest, DagsterRunReaction, SensorResult]],
    Sequence[RunRequest],
    SkipReason,
    RunRequest,
    DagsterRunReaction,
    SensorResult,
]
RawSensorEvaluationFunction: TypeAlias = Callable[..., RawSensorEvaluationFunctionReturn]

SensorEvaluationFunction: TypeAlias = Callable[..., Iterator[Union[SkipReason, RunRequest]]]


def get_context_param_name(fn: Callable) -> Optional[str]:
    """Determines the sensor's context parameter name by excluding all resource parameters."""
    resource_params = {param.name for param in get_resource_args(fn)}

    return next(
        (param.name for param in get_function_params(fn) if param.name not in resource_params), None
    )


def validate_and_get_resource_dict(
    resources: Resources, sensor_name: str, required_resource_keys: Set[str]
) -> Dict[str, Any]:
    """Validates that the context has all the required resources and returns a dictionary of
    resource key to resource object.
    """
    for k in required_resource_keys:
        if not hasattr(resources, k):
            raise DagsterInvalidDefinitionError(
                f"Resource with key '{k}' required by sensor '{sensor_name}' was not provided."
            )

    return {k: getattr(resources, k) for k in required_resource_keys}


def _check_dynamic_partitions_requests(
    dynamic_partitions_requests: Sequence[
        Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]
    ],
) -> None:
    req_keys_to_add_by_partitions_def_name = defaultdict(set)
    req_keys_to_delete_by_partitions_def_name = defaultdict(set)

    for req in dynamic_partitions_requests:
        duplicate_req_keys_to_delete = req_keys_to_delete_by_partitions_def_name.get(
            req.partitions_def_name, set()
        ).intersection(req.partition_keys)
        duplicate_req_keys_to_add = req_keys_to_add_by_partitions_def_name.get(
            req.partitions_def_name, set()
        ).intersection(req.partition_keys)
        if isinstance(req, AddDynamicPartitionsRequest):
            if duplicate_req_keys_to_delete:
                raise DagsterInvariantViolationError(
                    "Dynamic partition requests cannot contain both add and delete requests for"
                    " the same partition keys.Invalid request: partitions_def_name"
                    f" '{req.partitions_def_name}', partition_keys: {duplicate_req_keys_to_delete}"
                )
            elif duplicate_req_keys_to_add:
                raise DagsterInvariantViolationError(
                    "Cannot request to add duplicate dynamic partition keys: \npartitions_def_name"
                    f" '{req.partitions_def_name}', partition_keys: {duplicate_req_keys_to_add}"
                )
            req_keys_to_add_by_partitions_def_name[req.partitions_def_name].update(
                req.partition_keys
            )
        elif isinstance(req, DeleteDynamicPartitionsRequest):
            if duplicate_req_keys_to_delete:
                raise DagsterInvariantViolationError(
                    "Cannot request to add duplicate dynamic partition keys: \npartitions_def_name"
                    f" '{req.partitions_def_name}', partition_keys:"
                    f" {req_keys_to_add_by_partitions_def_name}"
                )
            elif duplicate_req_keys_to_add:
                raise DagsterInvariantViolationError(
                    "Dynamic partition requests cannot contain both add and delete requests for"
                    " the same partition keys.Invalid request: partitions_def_name"
                    f" '{req.partitions_def_name}', partition_keys: {duplicate_req_keys_to_add}"
                )
            req_keys_to_delete_by_partitions_def_name[req.partitions_def_name].update(
                req.partition_keys
            )
        else:
            check.failed(f"Unexpected dynamic partition request type: {req}")


class SensorDefinition(IHasInternalInit):
    """Define a sensor that initiates a set of runs based on some external state.

    Args:
        evaluation_fn (Callable[[SensorEvaluationContext]]): The core evaluation function for the
            sensor, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.SensorEvaluationContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        name (Optional[str]): The name of the sensor to create. Defaults to name of evaluation_fn
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[GraphDefinition, JobDefinition, UnresolvedAssetJob]): The job to execute when this sensor fires.
        jobs (Optional[Sequence[GraphDefinition, JobDefinition, UnresolvedAssetJob]]): (experimental) A list of jobs to execute when this sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        asset_selection (AssetSelection): (Experimental) an asset selection to launch a run for if
            the sensor condition is met. This can be provided instead of specifying a job.
    """

    def with_updated_jobs(self, new_jobs: Sequence[ExecutableDefinition]) -> "SensorDefinition":
        """Returns a copy of this sensor with the jobs replaced.

        Args:
            job (ExecutableDefinition): The job that should execute when this
                schedule runs.
        """
        return SensorDefinition.dagster_internal_init(
            name=self.name,
            evaluation_fn=self._evaluation_fn,
            minimum_interval_seconds=self.minimum_interval_seconds,
            description=self.description,
            job_name=None,  # if original init was passed job name, was resolved to a job
            jobs=new_jobs if len(new_jobs) > 1 else None,
            job=new_jobs[0] if len(new_jobs) == 1 else None,
            default_status=self.default_status,
            asset_selection=self.asset_selection,
            required_resource_keys=self.required_resource_keys,
        )

    def with_updated_job(self, new_job: ExecutableDefinition) -> "SensorDefinition":
        """Returns a copy of this sensor with the job replaced.

        Args:
            job (ExecutableDefinition): The job that should execute when this
                schedule runs.
        """
        return self.with_updated_jobs([new_job])

    def __init__(
        self,
        name: Optional[str] = None,
        *,
        evaluation_fn: Optional[RawSensorEvaluationFunction] = None,
        job_name: Optional[str] = None,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        asset_selection: Optional[AssetSelection] = None,
        required_resource_keys: Optional[Set[str]] = None,
    ):
        from dagster._config.pythonic_config import validate_resource_annotated_function

        if evaluation_fn is None:
            raise DagsterInvalidDefinitionError("Must provide evaluation_fn to SensorDefinition.")

        if (
            sum(
                [
                    int(job is not None),
                    int(jobs is not None),
                    int(job_name is not None),
                    int(asset_selection is not None),
                ]
            )
            > 1
        ):
            raise DagsterInvalidDefinitionError(
                "Attempted to provide more than one of 'job', 'jobs', 'job_name', and "
                "'asset_selection' params to SensorDefinition. Must provide only one."
            )

        jobs = jobs if jobs else [job] if job else None

        targets: Optional[List[Union[RepoRelativeTarget, DirectTarget]]] = None
        if job_name:
            targets = [
                RepoRelativeTarget(
                    job_name=check.str_param(job_name, "job_name"),
                    solid_selection=None,
                )
            ]
        elif job:
            targets = [DirectTarget(job)]
        elif jobs:
            targets = [DirectTarget(job) for job in jobs]
        elif asset_selection:
            targets = []

        if name:
            self._name = check_valid_name(name)
        else:
            self._name = evaluation_fn.__name__

        self._raw_fn: RawSensorEvaluationFunction = check.callable_param(
            evaluation_fn, "evaluation_fn"
        )
        self._evaluation_fn: Union[
            SensorEvaluationFunction,
            Callable[
                [SensorEvaluationContext],
                Iterator[Union[SkipReason, RunRequest, DagsterRunReaction]],
            ],
        ] = wrap_sensor_evaluation(self._name, evaluation_fn)
        self._min_interval = check.opt_int_param(
            minimum_interval_seconds, "minimum_interval_seconds", DEFAULT_SENSOR_DAEMON_INTERVAL
        )
        self._description = check.opt_str_param(description, "description")
        self._targets: Sequence[Union[RepoRelativeTarget, DirectTarget]] = check.opt_list_param(
            targets, "targets", (DirectTarget, RepoRelativeTarget)
        )
        self._default_status = check.inst_param(
            default_status, "default_status", DefaultSensorStatus
        )
        self._asset_selection = check.opt_inst_param(
            asset_selection, "asset_selection", AssetSelection
        )
        validate_resource_annotated_function(self._raw_fn)
        resource_arg_names: Set[str] = {arg.name for arg in get_resource_args(self._raw_fn)}

        check.param_invariant(
            len(required_resource_keys or []) == 0 or len(resource_arg_names) == 0,
            (
                "Cannot specify resource requirements in both @sensor decorator and as arguments to"
                " the decorated function"
            ),
        )
        self._required_resource_keys = (
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            or resource_arg_names
        )

    @staticmethod
    def dagster_internal_init(
        *,
        name: Optional[str],
        evaluation_fn: Optional[RawSensorEvaluationFunction],
        job_name: Optional[str],
        minimum_interval_seconds: Optional[int],
        description: Optional[str],
        job: Optional[ExecutableDefinition],
        jobs: Optional[Sequence[ExecutableDefinition]],
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        asset_selection: Optional[AssetSelection],
        required_resource_keys: Optional[Set[str]],
    ) -> "SensorDefinition":
        return SensorDefinition(
            name=name,
            evaluation_fn=evaluation_fn,
            job_name=job_name,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
            asset_selection=asset_selection,
            required_resource_keys=required_resource_keys,
        )

    def __call__(self, *args, **kwargs) -> RawSensorEvaluationFunctionReturn:
        context_param_name_if_present = get_context_param_name(self._raw_fn)
        context = get_or_create_sensor_context(self._raw_fn, *args, **kwargs)

        context_param = (
            {context_param_name_if_present: context} if context_param_name_if_present else {}
        )

        resources = validate_and_get_resource_dict(
            context.resources, self.name, self._required_resource_keys
        )
        return self._raw_fn(**context_param, **resources)

    @public
    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @public
    @property
    def name(self) -> str:
        return self._name

    @public
    @property
    def description(self) -> Optional[str]:
        return self._description

    @public
    @property
    def minimum_interval_seconds(self) -> Optional[int]:
        return self._min_interval

    @property
    def targets(self) -> Sequence[Union[DirectTarget, RepoRelativeTarget]]:
        return self._targets

    @public
    @property
    def job(self) -> Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition]:
        if self._targets:
            if len(self._targets) == 1 and isinstance(self._targets[0], DirectTarget):
                return self._targets[0].target
            elif len(self._targets) > 1:
                raise DagsterInvalidDefinitionError(
                    "Job property not available when SensorDefinition has multiple jobs."
                )
        raise DagsterInvalidDefinitionError("No job was provided to SensorDefinition.")

    @public
    @property
    def jobs(self) -> List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition]]:
        if self._targets and all(isinstance(target, DirectTarget) for target in self._targets):
            return [target.target for target in self._targets]  # type: ignore  # (illegible conditional)
        raise DagsterInvalidDefinitionError("No job was provided to SensorDefinition.")

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.STANDARD

    def evaluate_tick(self, context: "SensorEvaluationContext") -> "SensorExecutionData":
        """Evaluate sensor using the provided context.

        Args:
            context (SensorEvaluationContext): The context with which to evaluate this sensor.

        Returns:
            SensorExecutionData: Contains list of run requests, or skip message if present.

        """
        context = check.inst_param(context, "context", SensorEvaluationContext)

        result = list(self._evaluation_fn(context))

        skip_message: Optional[str] = None
        run_requests: List[RunRequest] = []
        dagster_run_reactions: List[DagsterRunReaction] = []
        dynamic_partitions_requests: Optional[
            Sequence[Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]]
        ] = []
        updated_cursor = context.cursor

        if not result or result == [None]:
            skip_message = "Sensor function returned an empty result"
        elif len(result) == 1:
            item = result[0]
            check.inst(item, (SkipReason, RunRequest, DagsterRunReaction, SensorResult))

            if isinstance(item, SensorResult):
                run_requests = list(item.run_requests) if item.run_requests else []
                skip_message = (
                    item.skip_reason.skip_message
                    if item.skip_reason
                    else (None if run_requests else "Sensor function returned an empty result")
                )

                _check_dynamic_partitions_requests(
                    item.dynamic_partitions_requests or [],
                )
                dynamic_partitions_requests = item.dynamic_partitions_requests or []

                if item.cursor and context.cursor_updated:
                    raise DagsterInvariantViolationError(
                        "SensorResult.cursor cannot be set if context.update_cursor() was called."
                    )
                updated_cursor = item.cursor

            elif isinstance(item, RunRequest):
                run_requests = [item]
            elif isinstance(item, SkipReason):
                skip_message = item.skip_message if isinstance(item, SkipReason) else None
            elif isinstance(item, DagsterRunReaction):
                dagster_run_reactions = (
                    [cast(DagsterRunReaction, item)] if isinstance(item, DagsterRunReaction) else []
                )
            else:
                check.failed(f"Unexpected type {type(item)} in sensor result")
        else:
            if any(isinstance(item, SensorResult) for item in result):
                check.failed(
                    "When a SensorResult is returned from a sensor, it must be the only object"
                    " returned."
                )

            check.is_list(result, (SkipReason, RunRequest, DagsterRunReaction))
            has_skip = any(map(lambda x: isinstance(x, SkipReason), result))
            run_requests = [item for item in result if isinstance(item, RunRequest)]
            dagster_run_reactions = [
                item for item in result if isinstance(item, DagsterRunReaction)
            ]

            if has_skip:
                if len(run_requests) > 0:
                    check.failed(
                        "Expected a single SkipReason or one or more RunRequests: received both "
                        "RunRequest and SkipReason"
                    )
                elif len(dagster_run_reactions) > 0:
                    check.failed(
                        "Expected a single SkipReason or one or more DagsterRunReaction: "
                        "received both DagsterRunReaction and SkipReason"
                    )
                else:
                    check.failed("Expected a single SkipReason: received multiple SkipReasons")

        _check_dynamic_partitions_requests(dynamic_partitions_requests)
        resolved_run_requests = self.resolve_run_requests(
            run_requests, context, self._asset_selection, dynamic_partitions_requests
        )

        return SensorExecutionData(
            resolved_run_requests,
            skip_message,
            updated_cursor,
            dagster_run_reactions,
            captured_log_key=context.log_key if context.has_captured_logs() else None,
            dynamic_partitions_requests=dynamic_partitions_requests,
        )

    def has_loadable_targets(self) -> bool:
        for target in self._targets:
            if isinstance(target, DirectTarget):
                return True
        return False

    def load_targets(
        self,
    ) -> Sequence[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition]]:
        """Returns job/graph definitions that have been directly passed into the sensor definition.
        Any jobs or graphs that are referenced by name will not be loaded.
        """
        targets = []
        for target in self._targets:
            if isinstance(target, DirectTarget):
                targets.append(target.load())
        return targets

    def resolve_run_requests(
        self,
        run_requests: Sequence[RunRequest],
        context: SensorEvaluationContext,
        asset_selection: Optional[AssetSelection],
        dynamic_partitions_requests: Sequence[
            Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]
        ],
    ) -> Sequence[RunRequest]:
        def _get_repo_job_by_name(context: SensorEvaluationContext, job_name: str) -> JobDefinition:
            if context.repository_def is None:
                raise DagsterInvariantViolationError(
                    "Must provide repository def to build_sensor_context when yielding partitioned"
                    " run requests"
                )
            return context.repository_def.get_job(job_name)

        has_multiple_targets = len(self._targets) > 1
        target_names = [target.job_name for target in self._targets]

        if run_requests and len(self._targets) == 0 and not self._asset_selection:
            raise Exception(
                f"Error in sensor {self._name}: Sensor evaluation function returned a RunRequest "
                "for a sensor lacking a specified target (job_name, job, or jobs). Targets "
                "can be specified by providing job, jobs, or job_name to the @sensor "
                "decorator."
            )

        if asset_selection:
            run_requests = [
                *_run_requests_with_base_asset_jobs(run_requests, context, asset_selection)
            ]

        dynamic_partitions_store = (
            CachingDynamicPartitionsLoader(context.instance) if context.instance_ref else None
        )

        # Run requests may contain an invalid target, or a partition key that does not exist.
        # We will resolve these run requests, applying the target and partition config/tags.
        resolved_run_requests = []
        for run_request in run_requests:
            if run_request.job_name is None and has_multiple_targets:
                raise Exception(
                    f"Error in sensor {self._name}: Sensor returned a RunRequest that did not"
                    " specify job_name for the requested run. Expected one of:"
                    f" {target_names}"
                )
            elif (
                run_request.job_name
                and run_request.job_name not in target_names
                and not asset_selection
            ):
                raise Exception(
                    f"Error in sensor {self._name}: Sensor returned a RunRequest with job_name "
                    f"{run_request.job_name}. Expected one of: {target_names}"
                )

            if run_request.partition_key and not run_request.has_resolved_partition():
                selected_job = _get_repo_job_by_name(
                    context, run_request.job_name if run_request.job_name else target_names[0]
                )
                resolved_run_requests.append(
                    run_request.with_resolved_tags_and_config(
                        target_definition=selected_job,
                        current_time=None,
                        dynamic_partitions_store=dynamic_partitions_store,
                        dynamic_partitions_requests=dynamic_partitions_requests,
                    )
                )
            else:
                resolved_run_requests.append(run_request)

        return resolved_run_requests

    @property
    def _target(self) -> Optional[Union[DirectTarget, RepoRelativeTarget]]:
        return self._targets[0] if self._targets else None

    @public
    @property
    def job_name(self) -> Optional[str]:
        if len(self._targets) > 1:
            raise DagsterInvalidInvocationError(
                f"Cannot use `job_name` property for sensor {self.name}, which targets multiple"
                " jobs."
            )
        return self._targets[0].job_name

    @public
    @property
    def default_status(self) -> DefaultSensorStatus:
        return self._default_status

    @property
    def asset_selection(self) -> Optional[AssetSelection]:
        return self._asset_selection


@whitelist_for_serdes(
    storage_field_names={"dagster_run_reactions": "pipeline_run_reactions"},
)
class SensorExecutionData(
    NamedTuple(
        "_SensorExecutionData",
        [
            ("run_requests", Optional[Sequence[RunRequest]]),
            ("skip_message", Optional[str]),
            ("cursor", Optional[str]),
            ("dagster_run_reactions", Optional[Sequence[DagsterRunReaction]]),
            ("captured_log_key", Optional[Sequence[str]]),
            (
                "dynamic_partitions_requests",
                Optional[
                    Sequence[Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]]
                ],
            ),
        ],
    )
):
    dagster_run_reactions: Optional[Sequence[DagsterRunReaction]]

    def __new__(
        cls,
        run_requests: Optional[Sequence[RunRequest]] = None,
        skip_message: Optional[str] = None,
        cursor: Optional[str] = None,
        dagster_run_reactions: Optional[Sequence[DagsterRunReaction]] = None,
        captured_log_key: Optional[Sequence[str]] = None,
        dynamic_partitions_requests: Optional[
            Sequence[Union[AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest]]
        ] = None,
    ):
        check.opt_sequence_param(run_requests, "run_requests", RunRequest)
        check.opt_str_param(skip_message, "skip_message")
        check.opt_str_param(cursor, "cursor")
        check.opt_sequence_param(dagster_run_reactions, "dagster_run_reactions", DagsterRunReaction)
        check.opt_list_param(captured_log_key, "captured_log_key", str)
        check.opt_sequence_param(
            dynamic_partitions_requests,
            "dynamic_partitions_requests",
            (AddDynamicPartitionsRequest, DeleteDynamicPartitionsRequest),
        )
        check.invariant(
            not (run_requests and skip_message), "Found both skip data and run request data"
        )
        return super(SensorExecutionData, cls).__new__(
            cls,
            run_requests=run_requests,
            skip_message=skip_message,
            cursor=cursor,
            dagster_run_reactions=dagster_run_reactions,
            captured_log_key=captured_log_key,
            dynamic_partitions_requests=dynamic_partitions_requests,
        )


def wrap_sensor_evaluation(
    sensor_name: str,
    fn: RawSensorEvaluationFunction,
) -> SensorEvaluationFunction:
    resource_arg_names: Set[str] = {arg.name for arg in get_resource_args(fn)}

    def _wrapped_fn(context: SensorEvaluationContext):
        resource_args_populated = validate_and_get_resource_dict(
            context.resources, sensor_name, resource_arg_names
        )

        context_param_name_if_present = get_context_param_name(fn)
        context_param = (
            {context_param_name_if_present: context} if context_param_name_if_present else {}
        )
        result = fn(**context_param, **resource_args_populated)

        if inspect.isgenerator(result) or isinstance(result, list):
            for item in result:
                yield item
        elif isinstance(result, (SkipReason, RunRequest, SensorResult)):
            yield result

        elif result is not None:
            raise Exception(
                (
                    "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                    "{result} of type {type_}.  Should only return SkipReason or "
                    "RunRequest objects."
                ).format(sensor_name=sensor_name, result=result, type_=type(result))
            )

    return _wrapped_fn


def build_sensor_context(
    instance: Optional[DagsterInstance] = None,
    cursor: Optional[str] = None,
    repository_name: Optional[str] = None,
    repository_def: Optional["RepositoryDefinition"] = None,
    sensor_name: Optional[str] = None,
    resources: Optional[Mapping[str, object]] = None,
    definitions: Optional["Definitions"] = None,
) -> SensorEvaluationContext:
    """Builds sensor execution context using the provided parameters.

    This function can be used to provide a context to the invocation of a sensor definition.If
    provided, the dagster instance must be persistent; DagsterInstance.ephemeral() will result in an
    error.

    Args:
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A cursor value to provide to the evaluation of the sensor.
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.
        repository_def (Optional[RepositoryDefinition]): The repository that the sensor belongs to.
            If needed by the sensor top-level resource definitions will be pulled from this repository.
            You can provide either this or `definitions`.
        resources (Optional[Mapping[str, ResourceDefinition]]): A set of resource definitions
            to provide to the sensor. If passed, these will override any resource definitions
            provided by the repository.
        definitions (Optional[Definitions]): `Definitions` object that the sensor is defined in.
            If needed by the sensor, top-level resource definitions will be pulled from these
            definitions. You can provide either this or `repository_def`.

    Examples:
        .. code-block:: python

            context = build_sensor_context()
            my_sensor(context)

    """
    from dagster._core.definitions.definitions_class import Definitions
    from dagster._core.definitions.repository_definition import RepositoryDefinition
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    check.opt_str_param(repository_name, "repository_name")
    repository_def = normalize_to_repository(
        check.opt_inst_param(definitions, "definitions", Definitions),
        check.opt_inst_param(repository_def, "repository_def", RepositoryDefinition),
        error_on_none=False,
    )

    return SensorEvaluationContext(
        instance_ref=None,
        last_completion_time=None,
        last_run_key=None,
        cursor=cursor,
        repository_name=repository_name,
        instance=instance,
        repository_def=repository_def,
        sensor_name=sensor_name,
        resources=wrap_resources_for_execution(resources),
    )


T = TypeVar("T")


def get_sensor_context_from_args_or_kwargs(
    fn: Callable,
    args: Tuple[Any],
    kwargs: Dict[str, Any],
    context_type: Type[T],
) -> Optional[T]:
    from dagster._config.pythonic_config import is_coercible_to_resource

    context_param_name = get_context_param_name(fn)

    kwarg_keys_non_resource = set(kwargs.keys()) - {param.name for param in get_resource_args(fn)}
    if len(args) + len(kwarg_keys_non_resource) > 1:
        raise DagsterInvalidInvocationError(
            "Sensor invocation received multiple non-resource arguments. Only a first "
            "positional context parameter should be provided when invoking."
        )

    if any(is_coercible_to_resource(arg) for arg in args):
        raise DagsterInvalidInvocationError(
            "If directly invoking a sensor, you may not provide resources as"
            " positional"
            " arguments, only as keyword arguments."
        )

    context: Optional[T] = None

    if len(args) > 0:
        context = check.opt_inst(args[0], context_type)
    elif len(kwargs) > 0:
        if context_param_name and context_param_name not in kwargs:
            raise DagsterInvalidInvocationError(
                f"Sensor invocation expected argument '{context_param_name}'."
            )
        context = check.opt_inst(kwargs.get(context_param_name or "context"), context_type)
    elif context_param_name:
        # If the context parameter is present but no value was provided, we error
        raise DagsterInvalidInvocationError(
            "Sensor evaluation function expected context argument, but no context argument "
            "was provided when invoking."
        )

    return context


def get_or_create_sensor_context(
    fn: Callable,
    *args: Any,
    **kwargs: Any,
) -> SensorEvaluationContext:
    """Based on the passed resource function and the arguments passed to it, returns the
    user-passed SensorEvaluationContext or creates one if it is not passed.

    Raises an exception if the user passes more than one argument or if the user-provided
    function requires a context parameter but none is passed.
    """
    context = (
        get_sensor_context_from_args_or_kwargs(
            fn,
            args,
            kwargs,
            context_type=SensorEvaluationContext,
        )
        or build_sensor_context()
    )
    resource_args_from_kwargs = {}

    resource_args = {param.name for param in get_resource_args(fn)}
    for resource_arg in resource_args:
        if resource_arg in kwargs:
            resource_args_from_kwargs[resource_arg] = kwargs[resource_arg]

    if resource_args_from_kwargs:
        return context.merge_resources(resource_args_from_kwargs)

    return context


def _run_requests_with_base_asset_jobs(
    run_requests: Iterable[RunRequest],
    context: SensorEvaluationContext,
    outer_asset_selection: AssetSelection,
) -> Sequence[RunRequest]:
    """For sensors that target asset selections instead of jobs, finds the corresponding base asset
    for a selected set of assets.
    """
    asset_graph = context.repository_def.asset_graph  # type: ignore  # (possible none)
    result = []
    for run_request in run_requests:
        if run_request.asset_selection:
            asset_keys = run_request.asset_selection

            unexpected_asset_keys = (
                AssetSelection.keys(*asset_keys) - outer_asset_selection
            ).resolve(asset_graph)
            if unexpected_asset_keys:
                raise DagsterInvalidSubsetError(
                    "RunRequest includes asset keys that are not part of sensor's asset_selection:"
                    f" {unexpected_asset_keys}"
                )
        else:
            asset_keys = outer_asset_selection.resolve(asset_graph)

        base_job = context.repository_def.get_implicit_job_def_for_assets(asset_keys)  # type: ignore  # (possible none)
        result.append(
            run_request.with_replaced_attrs(
                job_name=base_job.name, asset_selection=list(asset_keys)  # type: ignore  # (possible none)
            )
        )

    return result
