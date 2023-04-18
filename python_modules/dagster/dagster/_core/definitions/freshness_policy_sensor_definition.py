from typing import TYPE_CHECKING, Callable, Dict, Mapping, NamedTuple, Optional, Set, cast

import pendulum

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.scoped_resources_builder import Resources, ScopedResourcesBuilder
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    FreshnessPolicySensorExecutionError,
    user_code_error_boundary,
)
from dagster._core.instance import DagsterInstance
from dagster._serdes import (
    serialize_value,
    whitelist_for_serdes,
)
from dagster._serdes.errors import DeserializationError
from dagster._serdes.serdes import deserialize_value
from dagster._seven import JSONDecodeError

from .sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SensorType,
    SkipReason,
    get_context_param_name,
    get_sensor_context_from_args_or_kwargs,
    validate_and_get_resource_dict,
)

if TYPE_CHECKING:
    pass


@whitelist_for_serdes
class FreshnessPolicySensorCursor(
    NamedTuple(
        "_FreshnessPolicySensorCursor",
        [("minutes_late_by_key_str", Mapping[str, Optional[float]])],
    )
):
    def __new__(cls, minutes_late_by_key_str: Mapping[str, Optional[float]]):
        return super(FreshnessPolicySensorCursor, cls).__new__(
            cls,
            minutes_late_by_key_str=check.mapping_param(
                minutes_late_by_key_str, "minutes_late_by_key_str", key_type=str
            ),
        )

    @staticmethod
    def is_valid(json_str: str) -> bool:
        try:
            deserialize_value(json_str, FreshnessPolicySensorCursor)
            return True
        except (JSONDecodeError, DeserializationError):
            return False

    @staticmethod
    def from_dict(
        minutes_late_by_key: Mapping[AssetKey, Optional[float]]
    ) -> "FreshnessPolicySensorCursor":
        return FreshnessPolicySensorCursor(
            minutes_late_by_key_str={k.to_user_string(): v for k, v in minutes_late_by_key.items()}
        )

    @property
    def minutes_late_by_key(self) -> Mapping[AssetKey, Optional[float]]:
        return {AssetKey.from_user_string(k): v for k, v in self.minutes_late_by_key_str.items()}

    def to_json(self) -> str:
        return serialize_value(cast(NamedTuple, self))

    @staticmethod
    def from_json(json_str: str) -> "FreshnessPolicySensorCursor":
        return deserialize_value(json_str, FreshnessPolicySensorCursor)


class FreshnessPolicySensorContext(
    NamedTuple(
        "_FreshnessPolicySensorContext",
        [
            ("sensor_name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("freshness_policy", PublicAttr[FreshnessPolicy]),
            ("minutes_overdue", PublicAttr[Optional[float]]),
            ("previous_minutes_overdue", PublicAttr[Optional[float]]),
            ("instance", PublicAttr[DagsterInstance]),
            ("resources", Resources),
        ],
    )
):
    """The ``context`` object available to a decorated function of ``freshness_policy_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        asset_key (AssetKey): the key of the asset being monitored
        freshness_policy (FreshnessPolicy): the freshness policy of the asset being monitored
        minutes_overdue (Optional[float])
        previous_minutes_overdue (Optional[float]): the minutes_overdue value for this asset on the
            previous sensor tick.
        instance (DagsterInstance): the current instance.
    """

    def __new__(
        cls,
        sensor_name: str,
        asset_key: AssetKey,
        freshness_policy: FreshnessPolicy,
        minutes_overdue: Optional[float],
        previous_minutes_overdue: Optional[float],
        instance: DagsterInstance,
        resources: Optional[Resources] = None,
    ):
        minutes_overdue = check.opt_numeric_param(minutes_overdue, "minutes_overdue")
        previous_minutes_overdue = check.opt_numeric_param(
            previous_minutes_overdue, "previous_minutes_overdue"
        )
        return super(FreshnessPolicySensorContext, cls).__new__(
            cls,
            sensor_name=check.str_param(sensor_name, "sensor_name"),
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            freshness_policy=check.inst_param(freshness_policy, "FreshnessPolicy", FreshnessPolicy),
            minutes_overdue=float(minutes_overdue) if minutes_overdue is not None else None,
            previous_minutes_overdue=float(previous_minutes_overdue)
            if previous_minutes_overdue is not None
            else None,
            instance=check.inst_param(instance, "instance", DagsterInstance),
            resources=resources or ScopedResourcesBuilder.build_empty(),
        )


@experimental
def build_freshness_policy_sensor_context(
    sensor_name: str,
    asset_key: AssetKey,
    freshness_policy: FreshnessPolicy,
    minutes_overdue: Optional[float],
    previous_minutes_overdue: Optional[float] = None,
    instance: Optional[DagsterInstance] = None,
    resources: Optional[Resources] = None,
) -> FreshnessPolicySensorContext:
    """Builds freshness policy sensor context from provided parameters.

    This function can be used to provide the context argument when directly invoking a function
    decorated with `@freshness_policy_sensor`, such as when writing unit tests.

    Args:
        sensor_name (str): The name of the sensor the context is being constructed for.
        asset_key (AssetKey): The AssetKey for the monitored asset
        freshness_policy (FreshnessPolicy): The FreshnessPolicy for the monitored asset
        minutes_overdue (Optional[float]): How overdue the monitored asset currently is
        previous_minutes_overdue (Optional[float]): How overdue the monitored asset was on the
            previous tick.
        instance (DagsterInstance): The dagster instance configured for the context.

    Examples:
        .. code-block:: python

            context = build_freshness_policy_sensor_context(
                sensor_name="freshness_policy_sensor_to_invoke",
                asset_key=AssetKey("some_asset"),
                freshness_policy=FreshnessPolicy(maximum_lag_minutes=30)<
                minutes_overdue=10.0,
            )
            freshness_policy_sensor_to_invoke(context)
    """
    return FreshnessPolicySensorContext(
        sensor_name=sensor_name,
        asset_key=asset_key,
        freshness_policy=freshness_policy,
        minutes_overdue=minutes_overdue,
        previous_minutes_overdue=previous_minutes_overdue,
        instance=instance or DagsterInstance.ephemeral(),
        resources=resources,
    )


class FreshnessPolicySensorDefinition(SensorDefinition):
    """Define a sensor that reacts to the status of a given set of asset freshness policies,
    where the decorated function will be evaluated on every sensor tick.

    Args:
        name (str): The name of the sensor. Defaults to the name of the decorated function.
        freshness_policy_sensor_fn (Callable[[FreshnessPolicySensorContext], None]): The core
            evaluation function for the sensor. Takes a :py:class:`~dagster.FreshnessPolicySensorContext`.
        asset_selection (AssetSelection): The asset selection monitored by the sensor.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def __init__(
        self,
        name: str,
        asset_selection: AssetSelection,
        freshness_policy_sensor_fn: Callable[..., None],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        required_resource_keys: Optional[Set[str]] = None,
    ):
        check.str_param(name, "name")
        check.inst_param(asset_selection, "asset_selection", AssetSelection)
        check.opt_int_param(minimum_interval_seconds, "minimum_interval_seconds")
        check.opt_str_param(description, "description")
        check.inst_param(default_status, "default_status", DefaultSensorStatus)

        self._freshness_policy_sensor_fn = check.callable_param(
            freshness_policy_sensor_fn, "freshness_policy_sensor_fn"
        )

        resource_arg_names: Set[str] = {
            arg.name for arg in get_resource_args(freshness_policy_sensor_fn)
        }

        combined_required_resource_keys = (
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            | resource_arg_names
        )

        def _wrapped_fn(context: SensorEvaluationContext):
            from dagster._utils.caching_instance_queryer import (
                CachingInstanceQueryer,  # expensive import
            )

            if context.repository_def is None:
                raise DagsterInvalidInvocationError(
                    "The `repository_def` property on the `SensorEvaluationContext` passed into a "
                    "`FreshnessPolicySensorDefinition` must not be None."
                )

            if context.cursor is None or not FreshnessPolicySensorCursor.is_valid(context.cursor):
                new_cursor = FreshnessPolicySensorCursor({})
                context.update_cursor(new_cursor.to_json())
                yield SkipReason(f"Initializing {name}.")
                return

            evaluation_time = pendulum.now("UTC")
            asset_graph = context.repository_def.asset_graph
            instance_queryer = CachingInstanceQueryer(context.instance)
            data_time_resolver = CachingDataTimeResolver(
                instance_queryer=instance_queryer, asset_graph=asset_graph
            )
            monitored_keys = asset_selection.resolve(asset_graph)

            # get the previous status from the cursor
            previous_minutes_late_by_key = FreshnessPolicySensorCursor.from_json(
                context.cursor
            ).minutes_late_by_key

            minutes_late_by_key: Dict[AssetKey, Optional[float]] = {}
            for asset_key in monitored_keys:
                freshness_policy = asset_graph.freshness_policies_by_key.get(asset_key)
                if freshness_policy is None:
                    continue

                # get the current minutes_overdue value for this asset
                minutes_late_by_key[asset_key] = data_time_resolver.get_current_minutes_late(
                    evaluation_time=evaluation_time,
                    asset_key=asset_key,
                )

                resource_args_populated = validate_and_get_resource_dict(
                    context.resources, name, resource_arg_names
                )
                context_param_name = get_context_param_name(freshness_policy_sensor_fn)
                freshness_context = FreshnessPolicySensorContext(
                    sensor_name=name,
                    asset_key=asset_key,
                    freshness_policy=freshness_policy,
                    minutes_overdue=minutes_late_by_key[asset_key],
                    previous_minutes_overdue=previous_minutes_late_by_key.get(asset_key),
                    instance=context.instance,
                    resources=context.resources,
                )

                with user_code_error_boundary(
                    FreshnessPolicySensorExecutionError,
                    lambda: f'Error occurred during the execution of sensor "{name}".',
                ):
                    context_param = (
                        {context_param_name: freshness_context} if context_param_name else {}
                    )
                    result = freshness_policy_sensor_fn(
                        **context_param,
                        **resource_args_populated,
                    )
                if result is not None:
                    raise DagsterInvalidDefinitionError(
                        "Functions decorated by `@freshness_policy_sensor` may not return or yield"
                        " a value."
                    )

            context.update_cursor(
                FreshnessPolicySensorCursor.from_dict(minutes_late_by_key).to_json()
            )

        super(FreshnessPolicySensorDefinition, self).__init__(
            name=name,
            evaluation_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
            required_resource_keys=combined_required_resource_keys,
        )

    def __call__(self, *args, **kwargs) -> None:
        context_param_name = get_context_param_name(self._freshness_policy_sensor_fn)

        sensor_context = get_sensor_context_from_args_or_kwargs(
            self._freshness_policy_sensor_fn,
            args,
            kwargs,
            context_type=FreshnessPolicySensorContext,
        )
        context_param = (
            {context_param_name: sensor_context} if context_param_name and sensor_context else {}
        )

        resources = validate_and_get_resource_dict(
            sensor_context.resources if sensor_context else ScopedResourcesBuilder.build_empty(),
            self._name,
            self._required_resource_keys,
        )

        return self._freshness_policy_sensor_fn(**context_param, **resources)

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.FRESHNESS_POLICY


@experimental
def freshness_policy_sensor(
    asset_selection: AssetSelection,
    *,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[[Callable[..., None]], FreshnessPolicySensorDefinition,]:
    """Define a sensor that reacts to the status of a given set of asset freshness policies, where the
    decorated function will be evaluated on every tick for each asset in the selection that has a
    FreshnessPolicy defined.

    Note: returning or yielding a value from the annotated function will result in an error.

    Takes a :py:class:`~dagster.FreshnessPolicySensorContext`.

    Args:
        asset_selection (AssetSelection): The asset selection monitored by the sensor.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated function.
        freshness_policy_sensor_fn (Callable[[FreshnessPolicySensorContext], None]): The core
            evaluation function for the sensor. Takes a :py:class:`~dagster.FreshnessPolicySensorContext`.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def inner(fn: Callable[..., None]) -> FreshnessPolicySensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        return FreshnessPolicySensorDefinition(
            name=sensor_name,
            freshness_policy_sensor_fn=fn,
            asset_selection=asset_selection,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
        )

    return inner
