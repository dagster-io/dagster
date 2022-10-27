import inspect
import json
from typing import TYPE_CHECKING, Callable, Dict, List, Mapping, Optional, Sequence

import pendulum

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef

from ..decorator_utils import get_function_params
from .events import AssetKey
from .run_request import RunRequest, SkipReason
from .sensor_definition import (
    AssetMaterializationFunctionReturn,
    DefaultSensorStatus,
    RawSensorEvaluationFunctionReturn,
    SensorDefinition,
    SensorEvaluationContext,
    is_context_provided,
)
from .target import ExecutableDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryDefinition

FreshnessPolicyMaterializationFunction = Callable[
    ["FreshnessPolicySensorEvaluationContext"],
    AssetMaterializationFunctionReturn,
]


@experimental
class FreshnessPolicySensorEvaluationContext(SensorEvaluationContext):
    """The context object available as the argument to the evaluation function of a
    :py:class:`dagster.FreshnessPolicySensorDefinition`.

    Users should not instantiate this object directly. To construct a
    `FreshnessPolicySensorEvaluationContext` for testing purposes, use :py:func:`dagster.
    build_freshness_policy_sensor_context`.

    Attributes:
        asset_keys (Sequence[AssetKey]): The asset keys that the sensor is configured to monitor.
        repository_def (RepositoryDefinition): The repository that the sensor belongs to.
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        cursor (Optional[str]): The cursor, passed back from the last sensor evaluation via
            the cursor attribute of SkipReason and RunRequest.
        instance (Optional[DagsterInstance]): The deserialized instance can also be passed in
            directly (primarily useful in testing contexts).

    Example:

    .. code-block:: python

        from dagster import freshness_policy_sensor, FreshnessPolicySensorEvaluationContext

        @freshness_policy_sensor(asset_keys=[AssetKey("asset_1), AssetKey("asset_2)])
        def the_sensor(context: FreshnessPolicySensorEvaluationContext):
            ...

    """

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        cursor: Optional[str],
        repository_def: "RepositoryDefinition",
        asset_selection: Optional[AssetSelection],
        asset_keys: Optional[Sequence[AssetKey]],
        instance: Optional[DagsterInstance] = None,
    ):
        from dagster._core.selector.subset_selector import generate_asset_dep_graph

        self._repository_def = repository_def
        repo_assets = self._repository_def._assets_defs_by_key.values()
        repo_source_assets = self._repository_def.source_assets_by_key.values()
        self._upstream_mapping = generate_asset_dep_graph(repo_assets, repo_source_assets)[
            "upstream"
        ]
        if asset_selection is not None:
            self._asset_keys = list(asset_selection.resolve([*repo_assets, *repo_source_assets]))
        elif asset_keys is not None:
            self._asset_keys = list(asset_keys)
        else:
            raise DagsterInvalidDefinitionError(
                "FreshnessPolicySensorEvaluationContext requires one of asset_selection or asset_keys"
            )

        self._assets_by_key: Dict[AssetKey, Optional[AssetsDefinition]] = {}
        for asset_key in self._asset_keys:
            assets_def = (
                self._repository_def._assets_defs_by_key.get(  # pylint:disable=protected-access
                    asset_key
                )
            )
            if assets_def is None:
                raise DagsterInvalidDefinitionError(
                    f"{asset_key} was not found in the provided RepositoryDefinition when constructing "
                    "FreshnessPolicySensorEvaluationContext."
                )
            self._assets_by_key[asset_key] = assets_def

        self._previous_statuses_by_key = (
            {AssetKey.from_user_string(k): v for k, v in json.loads(cursor).items()}
            if cursor
            else {}
        )

        super().__init__(
            instance_ref=instance_ref,
            last_completion_time=None,
            last_run_key=None,
            cursor=cursor,
            repository_name=repository_def.name,
            instance=instance,
        )

    def current_minutes_late_by_key(self) -> Mapping[AssetKey, Optional[float]]:
        """Returns a mapping from each monitored AssetKey with a FreshnessPolicy defined to a number
        of minutes by which this asset is out of date with respect to its policy.
        """
        from dagster._core.execution.calculate_data_time import (
            get_upstream_materialization_times_for_key,
        )

        current_time = pendulum.now()

        statuses = {}
        for asset_key, assets_def in self._assets_by_key.items():
            if assets_def is None:
                continue
            freshness_policy = assets_def.freshness_policies_by_key.get(asset_key)
            if freshness_policy is None:
                continue
            root_data_ids_and_timestamps = get_upstream_materialization_times_for_key(
                instance=self.instance,
                asset_key=asset_key,
                upstream_asset_key_mapping=self._upstream_mapping,
            )
            statuses[asset_key] = freshness_policy.minutes_late(
                evaluation_time=current_time,
                upstream_materialization_times={
                    AssetKey.from_user_string(k): v[1]
                    for k, v in root_data_ids_and_timestamps.items()
                },
            )

        # update cursor with new information
        self.update_cursor(json.dumps({k.to_user_string(): v for k, v in statuses.items()}))
        return statuses

    def changed_freshness_statuses_by_key(self) -> Mapping[AssetKey, Optional[float]]:
        """Returns a mapping from each monitored AssetKey with a FreshnessPolicy defined to a number
        of minutes late.

        This mapping will contain keys for which the freshness status has changed (i.e. started or
        stopped being out of date) since the last tick on which statuses were evaluated.
        """
        return {
            key: minutes_late
            for key, minutes_late in self.current_minutes_late_by_key().items()
            if (self._previous_statuses_by_key.get(key) == 0) != (minutes_late == 0)
        }

    def failing_freshness_statuses_by_key(self) -> Mapping[AssetKey, Optional[float]]:
        """Returns a mapping from each monitored AssetKey with a FreshnessPolicy defined to a number
        of minutes late.

        This mapping will contain keys for which the data is currently out of date with respect to
        their policy.
        """
        return {
            key: minutes_late
            for key, minutes_late in self.current_minutes_late_by_key().items()
            if minutes_late != 0
        }


@experimental
class FreshnessPolicySensorDefinition(SensorDefinition):
    """Define an asset sensor that takes some action based on the SLA status of selected assets.

    Users should not instantiate this object directly. To construct a
    `FreshnessPolicySensor`, use :py:func:`dagster.
    freshness_policy_sensor`.

    Args:
        name (str): The name of the sensor to create.
        asset_keys (Sequence[AssetKey]): The asset_keys this sensor monitors.
        asset_materialization_fn (Callable[[FreshnessPolicySensorEvaluationContext], Union[Iterator[Union[RunRequest, SkipReason]], RunRequest, SkipReason]]): The core
            evaluation function for the sensor, which is run at an interval to determine whether a
            run should be launched or not. Takes a :py:class:`~dagster.FreshnessPolicySensorEvaluationContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The job
            object to target with this sensor.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            (experimental) A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def __init__(
        self,
        name: str,
        asset_keys: Optional[Sequence[AssetKey]],
        asset_selection: Optional[AssetSelection],
        job_name: Optional[str],
        asset_materialization_fn: Callable[
            ["FreshnessPolicySensorEvaluationContext"],
            RawSensorEvaluationFunctionReturn,
        ],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):

        check.invariant(asset_keys or asset_selection, "Must provide asset_keys or asset_selection")
        self._asset_selection: Optional[AssetSelection] = None
        self._asset_keys: Optional[List[AssetKey]] = None
        if asset_selection:
            self._asset_selection = check.inst_param(
                asset_selection, "asset_selection", AssetSelection
            )
        else:  # asset keys provided
            asset_keys = check.opt_list_param(asset_keys, "asset_keys", of_type=AssetKey)
            self._asset_keys = asset_keys

        def _wrap_asset_fn(materialization_fn):
            def _fn(context):
                result = materialization_fn(context)
                if inspect.isgenerator(result) or isinstance(result, list):
                    for item in result:
                        yield item
                elif isinstance(result, (SkipReason, RunRequest)):
                    yield result

            return _fn

        super().__init__(
            name=check_valid_name(name),
            job_name=job_name,
            evaluation_fn=_wrap_asset_fn(
                check.callable_param(asset_materialization_fn, "asset_materialization_fn")
            ),
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
        )

    def __call__(self, *args, **kwargs):

        if is_context_provided(self._raw_fn):
            if len(args) + len(kwargs) == 0:
                raise DagsterInvalidInvocationError(
                    "Sensor evaluation function expected context argument, but no context argument "
                    "was provided when invoking."
                )
            if len(args) + len(kwargs) > 1:
                raise DagsterInvalidInvocationError(
                    "Sensor invocation received multiple arguments. Only a first "
                    "positional context parameter should be provided when invoking."
                )

            context_param_name = get_function_params(self._raw_fn)[0].name

            if args:
                context = check.inst_param(
                    args[0], context_param_name, FreshnessPolicySensorEvaluationContext
                )
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.inst_param(
                    kwargs[context_param_name],
                    context_param_name,
                    FreshnessPolicySensorEvaluationContext,
                )

            return self._raw_fn(context)

        else:
            if len(args) + len(kwargs) > 0:
                raise DagsterInvalidInvocationError(
                    "Sensor decorated function has no arguments, but arguments were provided to "
                    "invocation."
                )

            return self._raw_fn()  # type: ignore [TypeGuard limitation]

    @public  # type: ignore
    @property
    def asset_selection(self) -> Optional[AssetSelection]:
        return self._asset_selection

    @public  # type: ignore
    @property
    def asset_keys(self) -> Optional[Sequence[AssetKey]]:
        return self._asset_keys


@experimental
def build_freshness_policy_sensor_context(
    *,
    repository_def: "RepositoryDefinition",
    asset_keys: Optional[Sequence[AssetKey]] = None,
    asset_selection: Optional[AssetSelection] = None,
    instance: Optional[DagsterInstance] = None,
    cursor: Optional[str] = None,
) -> FreshnessPolicySensorEvaluationContext:
    """Builds freshness policy sensor execution context for testing purposes using the provided parameters.

    This function can be used to provide a context to the invocation of a multi asset sensor definition. If
    provided, the dagster instance must be persistent; DagsterInstance.ephemeral() will result in an
    error.

    Args:
        repository_def (RepositoryDefinition): The repository definition that the sensor belongs to.
        asset_keys (Optional[Sequence[AssetKey]]): The list of asset keys monitored by the sensor.
            If not provided, asset_selection argument must be provided.
        asset_selection (Optional[AssetSelection]): The asset selection monitored by the sensor.
            If not provided, asset_keys argument must be provided.
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A string cursor to provide to the evaluation of the sensor. Must be
            a dictionary of asset key strings to ints that has been converted to a json string

    Examples:

        .. code-block:: python

            @repository
            def my_repo():
                ...

            with instance_for_test() as instance:
                context = build_freshness_policy_sensor_context(
                    repository_def=my_repo,
                    asset_keys=[AssetKey("asset_1"), AssetKey("asset_2")],
                    instance=instance,
                )
                my_freshness_policy_sensor(context)

    """
    from dagster._core.definitions import RepositoryDefinition

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)
    check.invariant(asset_keys or asset_selection, "Must provide asset_keys or asset_selection")

    if asset_selection:
        asset_selection = check.inst_param(asset_selection, "asset_selection", AssetSelection)
        asset_keys = None
    else:  # asset keys provided
        asset_keys = check.opt_list_param(asset_keys, "asset_keys", of_type=AssetKey)
        check.invariant(len(asset_keys) > 0, "Must provide at least one asset key")
        asset_selection = None

    return FreshnessPolicySensorEvaluationContext(
        instance_ref=None,
        asset_selection=asset_selection,
        asset_keys=asset_keys,
        cursor=cursor,
        instance=instance,
        repository_def=repository_def,
    )
