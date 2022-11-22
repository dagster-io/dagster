from typing import Callable, Dict, Mapping, NamedTuple, Optional, cast

import pendulum

import dagster._check as check
from dagster._annotations import PublicAttr, experimental
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    FreshnessPolicySensorExecutionError,
    user_code_error_boundary,
)
from dagster._core.instance import DagsterInstance
from dagster._serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster._serdes.errors import DeserializationError
from dagster._seven import JSONDecodeError
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from ..decorator_utils import get_function_params
from .sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
    is_context_provided,
)


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
            obj = deserialize_json_to_dagster_namedtuple(json_str)
            return isinstance(obj, FreshnessPolicySensorCursor)
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
        return serialize_dagster_namedtuple(cast(NamedTuple, self))

    @staticmethod
    def from_json(json_str: str) -> "FreshnessPolicySensorCursor":
        return cast(FreshnessPolicySensorCursor, deserialize_json_to_dagster_namedtuple(json_str))


class FreshnessPolicySensorContext(
    NamedTuple(
        "_FreshnessPolicySensorContext",
        [
            ("sensor_name", PublicAttr[str]),
            ("asset_key", PublicAttr[AssetKey]),
            ("freshness_policy", PublicAttr[FreshnessPolicy]),
            ("minutes_late", PublicAttr[Optional[float]]),
            ("previous_minutes_late", PublicAttr[Optional[float]]),
            ("instance", PublicAttr[DagsterInstance]),
        ],
    )
):
    """The ``context`` object available to a decorated function of ``freshness_policy_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        asset_key (AssetKey): the key of the asset being monitored
        freshness_policy (FreshnessPolicy): the freshness policy of the asset being monitored
        minutes_late (Optional[float])
        previous_minutes_late (Optional[float]): the minutes_late value for this asset on the
            previous sensor tick.
        instance (DagsterInstance): the current instance.
    """

    def __new__(
        cls,
        sensor_name: str,
        asset_key: AssetKey,
        freshness_policy: FreshnessPolicy,
        minutes_late: Optional[float],
        previous_minutes_late: Optional[float],
        instance: DagsterInstance,
    ):
        minutes_late = check.opt_numeric_param(minutes_late, "minutes_late")
        previous_minutes_late = check.opt_numeric_param(
            previous_minutes_late, "previous_minutes_late"
        )
        return super(FreshnessPolicySensorContext, cls).__new__(
            cls,
            sensor_name=check.str_param(sensor_name, "sensor_name"),
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            freshness_policy=check.inst_param(freshness_policy, "FreshnessPolicy", FreshnessPolicy),
            minutes_late=float(minutes_late) if minutes_late else None,
            previous_minutes_late=float(previous_minutes_late) if previous_minutes_late else None,
            instance=check.inst_param(instance, "instance", DagsterInstance),
        )


@experimental
def build_freshness_policy_sensor_context(
    sensor_name: str,
    asset_key: AssetKey,
    freshness_policy: FreshnessPolicy,
    minutes_late: Optional[float],
    previous_minutes_late: Optional[float] = None,
    instance: Optional[DagsterInstance] = None,
) -> FreshnessPolicySensorContext:
    """
    Builds freshness policy sensor context from provided parameters.

    This function can be used to provide the context argument when directly invoking a function
    decorated with `@freshness_policy_sensor`, such as when writing unit tests.

    Args:
        sensor_name (str): The name of the sensor the context is being constructed for.
        asset_key (AssetKey): The AssetKey for the monitored asset
        freshness_policy (FreshnessPolicy): The FreshnessPolicy for the monitored asset
        minutes_late (Optional[float]): How late the monitored asset currently is
        previous_minutes_late (Optional[float]): How late the monitored asset was on the previous
            tick.
        instance (DagsterInstance): The dagster instance configured for the context.

    Examples:
        .. code-block:: python

            context = build_freshness_policy_sensor_context(
                sensor_name="run_status_sensor_to_invoke",
                asset_key=AssetKey("some_asset"),
                freshness_policy=FreshnessPolicy(maximum_lag_minutes=30)<
                minutes_late=10.0,
            )
            run_status_sensor_to_invoke(context)
    """

    return FreshnessPolicySensorContext(
        sensor_name=sensor_name,
        asset_key=asset_key,
        freshness_policy=freshness_policy,
        minutes_late=minutes_late,
        previous_minutes_late=previous_minutes_late,
        instance=instance or DagsterInstance.ephemeral(),
    )


class FreshnessPolicySensorDefinition(SensorDefinition):
    """
    Define a sensor that reacts to the status of a given set of asset freshness policies,
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
        freshness_policy_sensor_fn: Callable[[FreshnessPolicySensorContext], None],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):

        check.str_param(name, "name")
        check.inst_param(asset_selection, "asset_selection", AssetSelection)
        check.opt_int_param(minimum_interval_seconds, "minimum_interval_seconds")
        check.opt_str_param(description, "description")
        check.inst_param(default_status, "default_status", DefaultSensorStatus)

        self._freshness_policy_sensor_fn = check.callable_param(
            freshness_policy_sensor_fn, "freshness_policy_sensor_fn"
        )

        def _wrapped_fn(context: SensorEvaluationContext):

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
            instance_queryer = CachingInstanceQueryer(context.instance)
            asset_graph = context.repository_def.asset_graph
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

                # get the current minutes_late value for this asset
                minutes_late_by_key[asset_key] = instance_queryer.get_current_minutes_late_for_key(
                    evaluation_time=evaluation_time,
                    asset_graph=asset_graph,
                    asset_key=asset_key,
                )

                with user_code_error_boundary(
                    FreshnessPolicySensorExecutionError,
                    lambda: f'Error occurred during the execution of sensor "{name}".',
                ):
                    result = freshness_policy_sensor_fn(
                        FreshnessPolicySensorContext(
                            sensor_name=name,
                            asset_key=asset_key,
                            freshness_policy=freshness_policy,
                            minutes_late=minutes_late_by_key[asset_key],
                            previous_minutes_late=previous_minutes_late_by_key.get(asset_key),
                            instance=context.instance,
                        )
                    )

                if result is not None:
                    raise DagsterInvalidDefinitionError(
                        "Functions decorated by `@freshness_policy_sensor` may not return or yield a value."
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
        )

    def __call__(self, *args, **kwargs):
        if is_context_provided(self._freshness_policy_sensor_fn):
            if len(args) + len(kwargs) == 0:
                raise DagsterInvalidInvocationError(
                    "Freshness policy sensor function expected context argument, but no context argument "
                    "was provided when invoking."
                )
            if len(args) + len(kwargs) > 1:
                raise DagsterInvalidInvocationError(
                    "Freshness policy sensor invocation received multiple arguments. Only a first "
                    "positional context parameter should be provided when invoking."
                )

            context_param_name = get_function_params(self._freshness_policy_sensor_fn)[0].name

            if args:
                context = check.opt_inst_param(
                    args[0], context_param_name, FreshnessPolicySensorContext
                )
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Freshness policy sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.opt_inst_param(
                    kwargs[context_param_name], context_param_name, FreshnessPolicySensorContext
                )

            if not context:
                raise DagsterInvalidInvocationError(
                    "Context must be provided for direct invocation of freshness policy sensor."
                )

            return self._freshness_policy_sensor_fn(context)

        else:
            raise DagsterInvalidDefinitionError(
                "Freshness policy sensor must accept a context argument."
            )


@experimental
def freshness_policy_sensor(
    asset_selection: AssetSelection,
    *,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[[Callable[[FreshnessPolicySensorContext], None]], FreshnessPolicySensorDefinition,]:
    """
    Define a sensor that reacts to the status of a given set of asset freshness policies, where the
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

    def inner(
        fn: Callable[[FreshnessPolicySensorContext], None]
    ) -> FreshnessPolicySensorDefinition:

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
