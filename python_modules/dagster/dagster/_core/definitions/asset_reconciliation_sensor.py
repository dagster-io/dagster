from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_daemon_context import (
    AssetDaemonCursor,
    AssetDaemonIteration,
    AutoMaterializeAssetEvaluation,
)
from dagster._core.definitions.events import AssetKey
from dagster._utils.backcompat import deprecation_warning

from .asset_graph import AssetGraph
from .asset_selection import AssetSelection
from .decorators.sensor_decorator import sensor
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


def reconcile(
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    instance: "DagsterInstance",
    cursor: AssetDaemonCursor,
    materialize_run_tags: Optional[Mapping[str, str]],
    observe_run_tags: Optional[Mapping[str, str]],
    auto_observe: bool,
) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation],]:
    context = AssetDaemonIteration(
        instance=instance,
        asset_graph=asset_graph,
        stored_cursor=cursor,
        target_asset_keys=target_asset_keys,
    )
    return context.evaluate(
        materialize_run_tags=materialize_run_tags,
        observe_run_tags=observe_run_tags,
        auto_observe=auto_observe,
    )


@experimental
def build_asset_reconciliation_sensor(
    asset_selection: AssetSelection,
    name: str = "asset_reconciliation_sensor",
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    run_tags: Optional[Mapping[str, str]] = None,
) -> SensorDefinition:
    r"""Constructs a sensor that will monitor the provided assets and launch materializations to
    "reconcile" them.

    An asset is considered "unreconciled" if any of:

    - This sensor has never tried to materialize it and it has never been materialized.

    - Any of its parents have been materialized more recently than it has.

    - Any of its parents are unreconciled.

    - It is not currently up to date with respect to its freshness policy.

    The sensor won't try to reconcile any assets before their parents are reconciled. When multiple
    FreshnessPolicies require data from the same upstream assets, this sensor will attempt to
    launch a minimal number of runs of that asset to satisfy all constraints.

    Args:
        asset_selection (AssetSelection): The group of assets you want to keep up-to-date
        name (str): The name to give the sensor.
        minimum_interval_seconds (Optional[int]): The minimum amount of time that should elapse between sensor invocations.
        description (Optional[str]): A description for the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        run_tags (Optional[Mapping[str, str]]): Dictionary of tags to pass to the RunRequests launched by this sensor

    Returns:
        SensorDefinition

    Example:
        If you have the following asset graph, with no freshness policies:

        .. code-block:: python

            a       b       c
             \     / \     /
                d       e
                 \     /
                    f

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.assets(d, e, f),
                name="my_reconciliation_sensor",
            )

        You will observe the following behavior:
            * If ``a``, ``b``, and ``c`` are all materialized, then on the next sensor tick, the sensor will see that ``d`` and ``e`` can
              be materialized. Since ``d`` and ``e`` will be materialized, ``f`` can also be materialized. The sensor will kick off a
              run that will materialize ``d``, ``e``, and ``f``.
            * If, on the next sensor tick, none of ``a``, ``b``, and ``c`` have been materialized again, the sensor will not launch a run.
            * If, before the next sensor tick, just asset ``a`` and ``b`` have been materialized, the sensor will launch a run to
              materialize ``d``, ``e``, and ``f``, because they're downstream of ``a`` and ``b``.
              Even though ``c`` hasn't been materialized, the downstream assets can still be
              updated, because ``c`` is still considered "reconciled".

    Example:
        If you have the following asset graph, with the following freshness policies:
            * ``c: FreshnessPolicy(maximum_lag_minutes=120, cron_schedule="0 2 \* \* \*")``, meaning
              that by 2AM, c needs to be materialized with data from a and b that is no more than 120
              minutes old (i.e. all of yesterday's data).

        .. code-block:: python

            a     b
             \   /
               c

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.all(),
                name="my_reconciliation_sensor",
            )

        Assume that ``c`` currently has incorporated all source data up to ``2022-01-01 23:00``.

        You will observe the following behavior:
            * At any time between ``2022-01-02 00:00`` and ``2022-01-02 02:00``, the sensor will see that
              ``c`` will soon require data from ``2022-01-02 00:00``. In order to satisfy this
              requirement, there must be a materialization for both ``a`` and ``b`` with time >=
              ``2022-01-02 00:00``. If such a materialization does not exist for one of those assets,
              the missing asset(s) will be executed on this tick, to help satisfy the constraint imposed
              by ``c``. Materializing ``c`` in the same run as those assets will satisfy its
              required data constraint, and so the sensor will kick off a run for ``c`` alongside
              whichever upstream assets did not have up-to-date data.
            * On the next tick, the sensor will see that a run is currently planned which will
              satisfy that constraint, so no runs will be kicked off.
            * Once that run completes, a new materialization event will exist for ``c``, which will
              incorporate all of the required data, so no new runs will be kicked off until the
              following day.


    """
    check_valid_name(name)
    check.opt_mapping_param(run_tags, "run_tags", key_type=str, value_type=str)
    deprecation_warning(
        "build_asset_reconciliation_sensor", "1.4", "Use AutoMaterializePolicys instead."
    )

    @sensor(
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
    def _sensor(context):
        asset_graph = context.repository_def.asset_graph
        cursor = (
            AssetDaemonCursor.from_serialized(context.cursor, asset_graph)
            if context.cursor
            else AssetDaemonCursor.empty()
        )

        # if there is a auto materialize policy set in the selection, filter down to that. Otherwise, use the
        # whole selection
        target_asset_keys = asset_selection.resolve(asset_graph)
        for target_key in target_asset_keys:
            check.invariant(
                asset_graph.get_auto_materialize_policy(target_key) is None,
                (
                    f"build_asset_reconciliation_sensor: Asset '{target_key.to_user_string()}' has"
                    " an AutoMaterializePolicy set. This asset will be automatically materialized"
                    " by the AssetDaemon, and should not be passed to this sensor. It's"
                    " recommended to remove this sensor once you have migrated to the"
                    " AutoMaterializePolicy api."
                ),
            )

        run_requests, updated_cursor, _ = reconcile(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=context.instance,
            cursor=cursor,
            materialize_run_tags=run_tags,
            observe_run_tags=None,
            auto_observe=False,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return _sensor
