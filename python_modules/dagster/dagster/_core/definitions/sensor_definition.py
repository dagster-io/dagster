import inspect
import json
from contextlib import ExitStack
from enum import Enum
from typing import (
    TYPE_CHECKING,
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
    Union,
    cast,
)

from typing_extensions import TypeGuard

import dagster._check as check
from dagster._annotations import experimental, public
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.instance import DagsterInstance
from dagster._core.instance.ref import InstanceRef
from dagster._serdes import whitelist_for_serdes

from ..decorator_utils import get_function_params
from .events import AssetKey
from .graph_definition import GraphDefinition
from .mode import DEFAULT_MODE_NAME
from .pipeline_definition import PipelineDefinition
from .run_request import PipelineRunReaction, RunRequest, SkipReason
from .target import DirectTarget, ExecutableDefinition, RepoRelativeTarget
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.definitions.repository_definition import RepositoryDefinition
    from dagster._core.events.log import EventLogEntry
    from dagster._core.storage.event_log.base import EventLogRecord


@whitelist_for_serdes
class DefaultSensorStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


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
        instance (Optional[DagsterInstance]): The deserialized instance can also be passed in
            directly (primarily useful in testing contexts).

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
        instance: Optional[DagsterInstance] = None,
    ):
        self._exit_stack = ExitStack()
        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )
        self._last_run_key = check.opt_str_param(last_run_key, "last_run_key")
        self._cursor = check.opt_str_param(cursor, "cursor")
        self._repository_name = check.opt_str_param(repository_name, "repository_name")
        self._instance = check.opt_inst_param(instance, "instance", DagsterInstance)

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    @public  # type: ignore
    @property
    def instance(self) -> DagsterInstance:
        # self._instance_ref should only ever be None when this SensorEvaluationContext was
        # constructed under test.
        if not self._instance:
            if not self._instance_ref:
                raise DagsterInvariantViolationError(
                    "Attempted to initialize dagster instance, but no instance reference was provided."
                )
            self._instance = self._exit_stack.enter_context(
                DagsterInstance.from_ref(self._instance_ref)
            )
        return cast(DagsterInstance, self._instance)

    @public  # type: ignore
    @property
    def last_completion_time(self) -> Optional[float]:
        return self._last_completion_time

    @public  # type: ignore
    @property
    def last_run_key(self) -> Optional[str]:
        return self._last_run_key

    @public  # type: ignore
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

    @public  # type: ignore
    @property
    def repository_name(self) -> Optional[str]:
        return self._repository_name


def _get_partition_key_from_event_log_record(event_log_record: "EventLogRecord") -> Optional[str]:
    """
    Given an event log record, returns the partition key for the event log record if it exists."""
    from dagster._core.storage.event_log.base import EventLogRecord

    check.inst_param(event_log_record, "event_log_record", EventLogRecord)

    dagster_event = event_log_record.event_log_entry.dagster_event
    if dagster_event:
        return dagster_event.partition
    return None


@experimental
class MultiAssetSensorEvaluationContext(SensorEvaluationContext):
    """The context object available as the argument to the evaluation function of a :py:class:`dagster.MultiAssetSensorDefinition`.

    Users should not instantiate this object directly. To construct a
    `MultiAssetSensorEvaluationContext` for testing purposes, use :py:func:`dagster.
    build_multi_asset_sensor_context`.

    Attributes:
        asset_keys (Sequence[AssetKey]): The asset keys that the sensor is configured to monitor.
        repository_def (RepositoryDefinition): The repository that the sensor belongs to.
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        cursor (Optional[str]): The cursor, passed back from the last sensor evaluation via
            the cursor attribute of SkipReason and RunRequest. Must be a dictionary of asset key strings to ints
            that has been converted to a json string
        last_completion_time (float): DEPRECATED The last time that the sensor was evaluated (UTC).
        last_run_key (str): DEPRECATED The run key of the RunRequest most recently created by this
            sensor. Use the preferred `cursor` attribute instead.
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.
        instance (Optional[DagsterInstance]): The deserialized instance can also be passed in
            directly (primarily useful in testing contexts).

    Example:

    .. code-block:: python

        from dagster import multi_asset_sensor, MultiAssetSensorEvaluationContext

        @multi_asset_sensor(asset_keys=[AssetKey("asset_1), AssetKey("asset_2)])
        def the_sensor(context: MultiAssetSensorEvaluationContext):
            ...

    """

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        repository_name: Optional[str],
        repository_def: "RepositoryDefinition",
        asset_keys: Sequence[AssetKey],
        instance: Optional[DagsterInstance] = None,
    ):
        self._repository_def = repository_def
        self._asset_keys = asset_keys

        self._assets_by_key: Dict[AssetKey, AssetsDefinition] = {}
        for asset_key in asset_keys:
            assets_def = (
                self._repository_def._assets_defs_by_key.get(  # pylint:disable=protected-access
                    asset_key
                )
            )
            if assets_def is None:
                raise DagsterInvalidDefinitionError(
                    f"No asset with {asset_key} found in repository"
                )
            self._assets_by_key[asset_key] = assets_def

        self._partitions_def_by_asset_key = {
            asset_key: asset_def.partitions_def
            for asset_key, asset_def in self._assets_by_key.items()
        }

        self.cursor_has_been_updated = False

        super(MultiAssetSensorEvaluationContext, self).__init__(
            instance_ref=instance_ref,
            last_completion_time=last_completion_time,
            last_run_key=last_run_key,
            cursor=cursor,
            repository_name=repository_name,
            instance=instance,
        )

    def _get_partitions_after_cursor(self, asset_key: AssetKey) -> List[str]:
        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        cursor_partition_key, _ = self._get_cursor(asset_key)

        partitions_def = self._partitions_def_by_asset_key.get(asset_key)

        if not isinstance(partitions_def, PartitionsDefinition):
            raise DagsterInvalidInvocationError(f"No partitions defined for asset key {asset_key}")

        partitions_to_fetch = list(partitions_def.get_partition_keys())

        if cursor_partition_key is not None:
            # Return partitions after the cursor partition, not including the cursor partition
            partitions_to_fetch = partitions_to_fetch[
                partitions_to_fetch.index(cursor_partition_key) + 1 :
            ]
        return partitions_to_fetch

    @public
    def latest_materialization_records_by_key(
        self,
        asset_keys: Optional[Sequence[AssetKey]] = None,
        after_cursor_partition: Optional[bool] = False,
    ) -> Mapping[AssetKey, Optional["EventLogRecord"]]:
        """Fetches the most recent materialization event record for each asset in asset_keys.

        Args:
            asset_keys (Optional[Sequence[AssetKey]]): list of asset keys to fetch events for. If not specified, the
                latest materialization will be fetched for all assets the multi_asset_sensor monitors.
            after_cursor_partition (Optional[bool]): If True, only materializations with partitions
                after the cursor's current partition will be returned. By default, set to False. For
                unpartitioned assets, this parameter is ignored.

        Returns: Mapping of AssetKey to EventLogRecord where the EventLogRecord is the latest materialization event for the asset. If there
            is no materialization event for the asset, the value in the mapping will be None.
        """
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        if asset_keys is None:
            asset_keys = self._asset_keys
        else:
            asset_keys = check.opt_list_param(asset_keys, "asset_keys", of_type=AssetKey)

        asset_event_records = {}
        for a in asset_keys:
            _, cursor = self._get_cursor(a)

            partitions_to_fetch = (
                self._get_partitions_after_cursor(a) if after_cursor_partition else None
            )

            event_records = self.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=a,
                    after_cursor=cursor,
                    asset_partitions=partitions_to_fetch,
                ),
                ascending=False,
                limit=1,
            )

            if event_records:
                asset_event_records[a] = event_records[0]
            else:
                asset_event_records[a] = None

        return asset_event_records

    @public
    def materialization_records_for_key(
        self, asset_key: AssetKey, limit: int, after_cursor_partition: Optional[bool] = False
    ) -> Iterable["EventLogRecord"]:
        """Fetches asset materialization event records for asset_key, with the earliest event first.

        Args:
            asset_key (AssetKey): The asset to fetch materialization events for
            limit (int): The number of events to fetch
            after_cursor_partition (Optional[bool]): If True, only materializations with partitions
                after the cursor's current partition will be returned. By default, set to False. For
                unpartitioned assets, this parameter is ignored.
        """
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        if asset_key not in self._assets_by_key:
            raise DagsterInvalidInvocationError(f"Asset key {asset_key} not monitored by sensor.")

        _, cursor = self._get_cursor(asset_key)

        partitions_to_fetch = (
            self._get_partitions_after_cursor(asset_key) if after_cursor_partition else None
        )

        return self.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=cursor,
                asset_partitions=partitions_to_fetch,
            ),
            ascending=True,
            limit=limit,
        )

    def _get_cursor(self, asset_key: AssetKey) -> Tuple[Optional[str], Optional[int]]:
        """
        The cursor maps stringified AssetKeys (str(asset_key)) to Tuples. The first value in the
        tuple is the partition of type str, representing the partition key. The second value in the
        tuple is the storage_id (int) of the materialization event for the asset that has been most
        recently processed by the sensor.

        For example, a multi_asset_sensor that monitors partitioned asset A would have a cursor:
        {
            str(asset_a.key): (partition_a, storage_id_a),
        }
        Where partition_a and storage_id_a are the partition and storage_id of the most recent
        materialization processed by the sensor.

        The cursor is stringified as a JSON object and then loaded as needed. This method accepts an
        asset key and returns the tuple containing partition key and storage ID for that asset. If
        no asset key is provided, the method returns back the unpacked cursor object.
        """
        check.inst_param(asset_key, "asset_key", AssetKey)
        unpacked_cursor = json.loads(self.cursor) if self.cursor else {}

        partition_key, cursor = unpacked_cursor.get(str(asset_key), (None, None))
        return partition_key, cursor

    @public
    def latest_materialization_records_by_partition(
        self,
        asset_key: AssetKey,
        after_cursor_partition: Optional[bool] = False,
    ) -> Mapping[str, "EventLogRecord"]:
        """
        Given an asset, returns a mapping of partition key to the latest materialization event
        for that partition. Fetches only materializations after the cursor.

        Args:
            asset_key (AssetKey): The asset to fetch events for.
            after_cursor_partition (Optional[bool]): If True, only materializations with partitions
                after the cursor's current partition will be returned. By default, set to False. For
                unpartitioned assets, this parameter is ignored.

        Returns:
            Mapping[str, EventLogRecord]:
                Mapping of AssetKey to a mapping of partitions to EventLogRecords where the
                EventLogRecord is the most recent materialization event for the partition.
                Filters for materializations in partitions after the cursor.

        Example:
            .. code-block:: python

                @asset(partitions_def=DailyPartitionsDefinition("2022-07-01"))
                def july_asset():
                    return 1

                @multi_asset_sensor(asset_keys=[july_asset.key])
                def my_sensor(context):
                    context.latest_materialization_records_by_partition(july_asset.key)

                # After materializing july_asset for 2022-07-05, latest_materialization_by_partition
                # returns {"2022-07-05": EventLogRecord(...)}

        """
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventLogRecord, EventRecordsFilter

        asset_key = check.inst_param(asset_key, "asset_key", AssetKey)

        if asset_key not in self._assets_by_key:
            raise DagsterInvalidInvocationError(
                f"Asset key {asset_key} not monitored in sensor definition"
            )

        partitions_def = self._partitions_def_by_asset_key.get(asset_key)

        materialization_by_partition: Dict[str, EventLogRecord] = {}
        if not isinstance(partitions_def, PartitionsDefinition):
            raise DagsterInvariantViolationError(
                "Cannot get latest materialization by partition for assets with no partitions"
            )
        else:
            _, cursor = self._get_cursor(asset_key)

            partitions_to_fetch = (
                self._get_partitions_after_cursor(asset_key)
                if after_cursor_partition
                else list(partitions_def.get_partition_keys())
            )

            partition_materializations = self.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=asset_key,
                    asset_partitions=partitions_to_fetch,
                    after_cursor=cursor,
                ),
            )
            for materialization in partition_materializations:
                # Only update if no previous materialization for this partition exists,
                # to ensure we return the most recent materialization for each partition.
                partition = _get_partition_key_from_event_log_record(materialization)

                if isinstance(partition, str) and partition not in materialization_by_partition:
                    materialization_by_partition[partition] = materialization

        return materialization_by_partition

    @public
    def get_cursor_partition(self, asset_key: Optional[AssetKey]) -> Optional[str]:
        """A utility method to get the current partition the cursor is on."""
        asset_key = check.opt_inst_param(asset_key, "asset_key", AssetKey)
        if asset_key not in self._asset_keys:
            raise DagsterInvalidInvocationError(
                "Provided asset key must correspond to a provided asset"
            )
        if asset_key:
            partition_key, _ = self._get_cursor(asset_key)
        elif self._asset_keys is not None and len(self._asset_keys) == 1:
            partition_key, _ = self._get_cursor(self._asset_keys[0])
        else:
            raise DagsterInvalidInvocationError(
                "Asset key must be provided when multiple assets are defined"
            )

        return partition_key

    @public
    def all_partitions_materialized(
        self, asset_key: AssetKey, partitions: Optional[Sequence[str]] = None
    ) -> bool:
        """
        A utility method to check if a provided list of partitions have been materialized
        for a particular asset. This method ignores the cursor and checks all materializations
        for the asset.

        Args:
            asset_key (AssetKey): The asset to check partitions for.
            partitions (Optional[Sequence[str]]): A list of partitions to check. If not provided,
                all partitions for the asset will be checked.

        Returns:
            bool: True if all selected partitions have been materialized, False otherwise.
        """

        check.inst_param(asset_key, "asset_key", AssetKey)

        materialization_count_by_partition = self.instance.get_materialization_count_by_partition(
            [asset_key]
        ).get(asset_key, {})
        if not partitions:
            if asset_key not in self._asset_keys:
                raise DagsterInvariantViolationError(
                    f"Asset key {asset_key} not monitored by sensor"
                )

            partitions_def = self._partitions_def_by_asset_key[asset_key]
            if not partitions_def:
                raise DagsterInvariantViolationError(
                    f"Asset key {asset_key} is not partitioned. Cannot check if partitions have been materialized."
                )
            partitions = partitions_def.get_partition_keys()

        return all(
            [materialization_count_by_partition.get(partition, 0) != 0 for partition in partitions]
        )

    def _get_asset(self, asset_key: AssetKey) -> AssetsDefinition:
        repository_assets = (
            self._repository_def._assets_defs_by_key  # pylint:disable=protected-access
        )
        if asset_key in self._assets_by_key:
            return self._assets_by_key[asset_key]
        elif asset_key in repository_assets:
            return repository_assets[asset_key]
        else:
            raise DagsterInvalidInvocationError(
                f"Asset key {asset_key} not monitored in sensor and does not exist in target jobs"
            )

    @public
    def get_downstream_partition_keys(
        self, partition_key: str, from_asset_key: AssetKey, to_asset_key: AssetKey
    ) -> Sequence[str]:
        """
        Converts a partition key from one asset to the corresponding partition key in a downstream
        asset. Uses the existing partition mapping between the upstream asset and the downstream
        asset if it exists, otherwise, uses the default partition mapping.

        Args:
            partition_key (str): The partition key to convert.
            from_asset_key (AssetKey): The asset key of the upstream asset, which the provided
                partition key belongs to.
            to_asset_key (AssetKey): The asset key of the downstream asset. The provided partition
                key will be mapped to partitions within this asset.

        Returns:
            Sequence[str]: A list of the corresponding downstream partitions in to_asset_key that
                partition_key maps to.
        """

        partition_key = check.str_param(partition_key, "partition_key")

        to_asset = self._get_asset(to_asset_key)
        from_asset = self._get_asset(from_asset_key)

        if not isinstance(to_asset.partitions_def, PartitionsDefinition):
            raise DagsterInvalidInvocationError(
                f"Asset key {to_asset_key} is not partitioned. Cannot get partition keys."
            )
        if not isinstance(from_asset.partitions_def, PartitionsDefinition):
            raise DagsterInvalidInvocationError(
                f"Asset key {from_asset_key} is not partitioned. Cannot get partition keys."
            )

        partition_mapping = to_asset.get_partition_mapping(from_asset_key)
        downstream_partition_key_range = (
            partition_mapping.get_downstream_partitions_for_partition_range(
                PartitionKeyRange(partition_key, partition_key),
                downstream_partitions_def=to_asset.partitions_def,
                upstream_partitions_def=from_asset.partitions_def,
            )
        )

        partition_keys = to_asset.partitions_def.get_partition_keys()
        if (
            downstream_partition_key_range.start not in partition_keys
            or downstream_partition_key_range.end not in partition_keys
        ):
            raise DagsterInvalidInvocationError(
                f"Mapped partition key {partition_key} to downstream partition key range "
                f"[{downstream_partition_key_range.start}...{downstream_partition_key_range.end}] "
                "which is not a valid range in the downstream partitions definition."
            )
        downstream_partitions = partition_keys[
            partition_keys.index(downstream_partition_key_range.start) : partition_keys.index(
                downstream_partition_key_range.end
            )
            + 1
        ]
        return downstream_partitions

    @public
    def advance_cursor(
        self, materialization_records_by_key: Mapping[AssetKey, Optional["EventLogRecord"]]
    ):
        """Advances the cursor for a group of AssetKeys based on the EventLogRecord provided for each AssetKey.

        Args:
            materialization_records_by_key (Mapping[AssetKey, Optional[EventLogRecord]]): Mapping of AssetKeys to EventLogRecord or None. If
                an EventLogRecord is provided, the cursor for the AssetKey will be updated and future calls to fetch asset materialization events
                will only fetch events more recent that the EventLogRecord. If None is provided, the cursor for the AssetKey will not be updated.
        """
        cursor_dict = json.loads(self.cursor) if self.cursor else {}
        check.dict_param(cursor_dict, "cursor_dict", key_type=AssetKey)

        update_dict = {
            str(k): (_get_partition_key_from_event_log_record(v), v.storage_id)
            if v
            else cursor_dict.get(str(k))
            for k, v in materialization_records_by_key.items()
        }
        cursor_str = json.dumps(update_dict)
        self._cursor = check.opt_str_param(cursor_str, "cursor")
        self.cursor_has_been_updated = True

    @public
    def advance_all_cursors(self):
        """Updates the cursor to the most recent materialization event for all assets monitored by the multi_asset_sensor"""
        materializations_by_key = self.latest_materialization_records_by_key()
        self.advance_cursor(materializations_by_key)

    @public  # type: ignore
    @property
    def assets_defs_by_key(self) -> Mapping[AssetKey, AssetsDefinition]:
        return self._assets_by_key


@experimental
class AssetSLASensorEvaluationContext(SensorEvaluationContext):
    """The context object available as the argument to the evaluation function of a :py:class:`dagster.AssetSLASensorDefinition`."""

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        last_completion_time: Optional[float],
        last_run_key: Optional[str],
        cursor: Optional[str],
        repository_name: Optional[str],
        repository_def: "RepositoryDefinition",
        asset_keys: Optional[Sequence[AssetKey]] = None,
        instance: Optional[DagsterInstance] = None,
    ):
        from dagster._core.selector.subset_selector import generate_asset_dep_graph

        self._repository_def = repository_def

        self._upstream_assets = generate_asset_dep_graph(
            self._repository_def._assets_defs_by_key.values(),
            self._repository_def.source_assets_by_key.values(),
        )["upstream"]

        self._assets_by_key: Dict[AssetKey, AssetsDefinition] = {}
        # if no asset_keys supplied, default to all
        for asset_key in asset_keys or repository_def._assets_defs_by_key.keys():
            assets_def = self._repository_def._assets_defs_by_key.get(asset_key)
            if assets_def is None:
                raise DagsterInvalidDefinitionError(
                    f"No asset with {asset_key} found in repository"
                )
            if not assets_def.slas_by_key.get(asset_key):
                continue
            self._assets_by_key[asset_key] = assets_def

        self._next_cursor = cursor

        super(AssetSLASensorEvaluationContext, self).__init__(
            instance_ref=instance_ref,
            last_completion_time=last_completion_time,
            last_run_key=last_run_key,
            cursor=cursor,
            repository_name=repository_name,
            instance=instance,
        )

    def _data_times_by_key(self) -> Mapping[AssetKey, Optional[float]]:
        """
        For each asset monitored by this sensor, calculate its "data time". The data time of an
        asset is the time of the earliest data that could be incorporated into the current state
        of the asset, calculated for each asset by comparing their latest timestamp to the latest
        parent timestamp that happened before that materialization (as you cannot incorporate parent
        data if that parent runs after you do).
        """
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        calculated_data_times: Dict[Tuple[AssetKey, Optional[float]], Optional[float]] = {}

        def _data_time_for_asset(
            key: AssetKey,
            as_of_timestamp: Optional[float] = None,
            current_run_keys: Optional[Set[AssetKey]] = None,
        ) -> Optional[float]:
            """Recursive helper function for calculating this data time. Keeps track of previously
            calculated values, as many assets end up traversing similar paths through the
            historical materialization graph, and these queries can be expensive.

            If an asset is materialized in the same run as its parents, there's no need to do
            separate queries to determine the "most recent asset materialization for the parent
            which happened before this asset materialization", as that materialization is assumed
            to be the materialization that occured within that run (it would be very hard for this
            not to be the case). In this way, we can "fast forward" through the asset graph in
            common cases (where most materialization events happen as part of larger runs).
            """
            index = (key, as_of_timestamp)

            # if we've already calculated the data time of this key as of this index, return it
            # instead of calculating it from scratch
            if index in calculated_data_times:
                return calculated_data_times[index]

            # this asset was not materialized in the current run, so find the latest materialization
            # that happened before as_of_timestamp
            if key not in (current_run_keys or {}):
                event_records = self.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=key,
                        before_timestamp=as_of_timestamp,
                    ),
                    ascending=False,
                    limit=1,
                )

                # if no record found, then break
                latest_asset_event = event_records[0] if event_records else None
                if not latest_asset_event:
                    calculated_data_times[index] = None
                    return None

                # found the latest event, while we're at it grab the start time of the run
                run_id = latest_asset_event.event_log_entry.run_id
                event_records = self.instance.get_records_for_run(
                    run_id, of_type=DagsterEventType.RUN_START, limit=1
                )
                run_record = event_records.records[0] if event_records else None
                if not run_record:
                    # might want to error here
                    calculated_data_times[index] = None
                    return None

                # update these values based on current run
                as_of_timestamp = run_record.event_log_entry.timestamp
                current_run_keys = {
                    record.event_log_entry.dagster_event.event_specific_data.materialization.asset_key
                    for record in self.instance.get_records_for_run(
                        run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION
                    ).records
                }

            # recurse over all the parents
            parents = self._upstream_assets[key.to_user_string()]
            if not parents:
                # use the timestamp of the current run
                calculated_data_times[index] = as_of_timestamp
            else:
                # your data time is the minimum data time of yourself and your parents
                data_time = as_of_timestamp
                if data_time is not None:
                    for p in parents:
                        parent_data_time = _data_time_for_asset(
                            AssetKey.from_user_string(p),
                            as_of_timestamp=as_of_timestamp,
                            current_run_keys=current_run_keys,
                        )
                        if parent_data_time is None:
                            data_time = None
                            break
                        data_time = min(data_time, parent_data_time)
                calculated_data_times[index] = data_time

            return calculated_data_times[index]

        return {
            asset_key: _data_time_for_asset(asset_key) for asset_key in self._assets_by_key.keys()
        }

    @property
    def next_cursor(self) -> Optional[str]:
        return self._next_cursor

    @public
    def current_statuses_by_key(self) -> Mapping[AssetKey, bool]:
        current_data_times: Mapping[AssetKey, Optional[float]] = self._data_times_by_key()

        asset_sla_statuses = {}
        for asset_key, assets_def in self._assets_by_key.items():
            sla = assets_def.slas_by_key.get(asset_key)
            if not sla:
                continue
            asset_sla_statuses[asset_key] = sla.is_passing(current_data_times.get(asset_key))

        self._next_cursor = json.dumps(
            {str(key): value for key, value in asset_sla_statuses.items()}
        )
        return asset_sla_statuses

    @public
    def previous_statuses_by_key(self) -> Mapping[AssetKey, bool]:
        if not self.cursor:
            return {}
        cursor_dict = json.loads(self.cursor)
        return {
            asset_key: cursor_dict.get(str(asset_key)) for asset_key in self._assets_by_key.keys()
        }

    @public
    def changed_statuses_by_key(self) -> Mapping[AssetKey, bool]:
        previous_statuses = self.previous_statuses_by_key()
        current_statuses = self.current_statuses_by_key()

        return {
            key: cur_status
            for key, cur_status in current_statuses.items()
            if previous_statuses.get(key) != cur_status
        }

    @public  # type: ignore
    @property
    def assets_defs_by_key(self) -> Mapping[AssetKey, "AssetsDefinition"]:
        return self._assets_by_key


# Preserve SensorExecutionContext for backcompat so type annotations don't break.
SensorExecutionContext = SensorEvaluationContext

RawSensorEvaluationFunctionReturn = Union[
    Iterator[Union[SkipReason, RunRequest]],
    Sequence[RunRequest],
    SkipReason,
    RunRequest,
    PipelineRunReaction,
]
RawSensorEvaluationFunction = Union[
    Callable[[], RawSensorEvaluationFunctionReturn],
    Callable[[SensorEvaluationContext], RawSensorEvaluationFunctionReturn],
]
SensorEvaluationFunction = Callable[
    [SensorEvaluationContext], Iterator[Union[SkipReason, RunRequest]]
]


def is_context_provided(
    fn: "RawSensorEvaluationFunction",
) -> TypeGuard[Callable[[SensorEvaluationContext], "RawSensorEvaluationFunctionReturn"]]:
    return len(get_function_params(fn)) == 1


class SensorDefinition:
    """Define a sensor that initiates a set of runs based on some external state

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
        job (Optional[GraphDefinition, JobDefinition]): The job to execute when this sensor fires.
        jobs (Optional[Sequence[GraphDefinition, JobDefinition]]): (experimental) A list of jobs to execute when this sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

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
    ):
        if evaluation_fn is None:
            raise DagsterInvalidDefinitionError("Must provide evaluation_fn to SensorDefinition.")

        if job and jobs:
            raise DagsterInvalidDefinitionError(
                "Attempted to provide both job and jobs to SensorDefinition. Must provide only one "
                "of the two."
            )

        job_param_name = "job" if job else "jobs"
        jobs = jobs if jobs else [job] if job else None

        if job_name and jobs:
            raise DagsterInvalidDefinitionError(
                f"Attempted to provide both job_name and {job_param_name} to "
                "SensorDefinition. Must provide only one of the two."
            )

        targets: Optional[List[Union[RepoRelativeTarget, DirectTarget]]] = None
        if job_name:
            targets = [
                RepoRelativeTarget(
                    pipeline_name=check.str_param(job_name, "job_name"),
                    mode=DEFAULT_MODE_NAME,
                    solid_selection=None,
                )
            ]
        elif job:
            targets = [DirectTarget(job)]
        elif jobs:
            targets = [DirectTarget(job) for job in jobs]

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
                Iterator[Union[SkipReason, RunRequest, PipelineRunReaction]],
            ],
        ] = wrap_sensor_evaluation(self._name, evaluation_fn)
        self._min_interval = check.opt_int_param(
            minimum_interval_seconds, "minimum_interval_seconds", DEFAULT_SENSOR_DAEMON_INTERVAL
        )
        self._description = check.opt_str_param(description, "description")
        self._targets = check.opt_list_param(targets, "targets", (DirectTarget, RepoRelativeTarget))
        self._default_status = check.inst_param(
            default_status, "default_status", DefaultSensorStatus
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
                context = check.opt_inst_param(args[0], context_param_name, SensorEvaluationContext)
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.opt_inst_param(
                    kwargs[context_param_name], context_param_name, SensorEvaluationContext
                )

            context = context if context else build_sensor_context()

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
    def name(self) -> str:
        return self._name

    @public  # type: ignore
    @property
    def description(self) -> Optional[str]:
        return self._description

    @public  # type: ignore
    @property
    def minimum_interval_seconds(self) -> Optional[int]:
        return self._min_interval

    @property
    def targets(self) -> Sequence[Union[DirectTarget, RepoRelativeTarget]]:
        return self._targets

    @public  # type: ignore
    @property
    def job(self) -> Union[PipelineDefinition, GraphDefinition, UnresolvedAssetJobDefinition]:
        if self._targets:
            if len(self._targets) == 1 and isinstance(self._targets[0], DirectTarget):
                return self._targets[0].target
            elif len(self._targets) > 1:
                raise DagsterInvalidDefinitionError(
                    "Job property not available when SensorDefinition has multiple jobs."
                )
        raise DagsterInvalidDefinitionError("No job was provided to SensorDefinition.")

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

        run_requests: List[RunRequest]
        pipeline_run_reactions: List[PipelineRunReaction]
        if not result or result == [None]:
            run_requests = []
            pipeline_run_reactions = []
            skip_message = "Sensor function returned an empty result"
        elif len(result) == 1:
            item = result[0]
            check.inst(item, (SkipReason, RunRequest, PipelineRunReaction))
            run_requests = [item] if isinstance(item, RunRequest) else []
            pipeline_run_reactions = (
                [cast(PipelineRunReaction, item)] if isinstance(item, PipelineRunReaction) else []
            )
            skip_message = item.skip_message if isinstance(item, SkipReason) else None
        else:
            check.is_list(result, (SkipReason, RunRequest, PipelineRunReaction))
            has_skip = any(map(lambda x: isinstance(x, SkipReason), result))
            run_requests = [item for item in result if isinstance(item, RunRequest)]
            pipeline_run_reactions = [
                item for item in result if isinstance(item, PipelineRunReaction)
            ]

            if has_skip:
                if len(run_requests) > 0:
                    check.failed(
                        "Expected a single SkipReason or one or more RunRequests: received both "
                        "RunRequest and SkipReason"
                    )
                elif len(pipeline_run_reactions) > 0:
                    check.failed(
                        "Expected a single SkipReason or one or more PipelineRunReaction: "
                        "received both PipelineRunReaction and SkipReason"
                    )
                else:
                    check.failed("Expected a single SkipReason: received multiple SkipReasons")

        self.check_valid_run_requests(run_requests)

        return SensorExecutionData(
            run_requests,
            skip_message,
            context.cursor,
            pipeline_run_reactions,
        )

    def has_loadable_targets(self) -> bool:
        for target in self._targets:
            if isinstance(target, DirectTarget):
                return True
        return False

    def load_targets(
        self,
    ) -> Sequence[Union[PipelineDefinition, GraphDefinition, UnresolvedAssetJobDefinition]]:
        targets = []
        for target in self._targets:
            if isinstance(target, DirectTarget):
                targets.append(target.load())
        return targets

    def check_valid_run_requests(self, run_requests: Sequence[RunRequest]):
        has_multiple_targets = len(self._targets) > 1
        target_names = [target.pipeline_name for target in self._targets]

        if run_requests and not self._targets:
            raise Exception(
                f"Error in sensor {self._name}: Sensor evaluation function returned a RunRequest "
                "for a sensor lacking a specified target (job_name, job, or jobs). Targets "
                "can be specified by providing job, jobs, or job_name to the @sensor "
                "decorator."
            )

        for run_request in run_requests:
            if run_request.job_name is None and has_multiple_targets:
                raise Exception(
                    f"Error in sensor {self._name}: Sensor returned a RunRequest that did not "
                    f"specify job_name for the requested run. Expected one of: {target_names}"
                )
            elif run_request.job_name and run_request.job_name not in target_names:
                raise Exception(
                    f"Error in sensor {self._name}: Sensor returned a RunRequest with job_name "
                    f"{run_request.job_name}. Expected one of: {target_names}"
                )

    @property
    def _target(self) -> Optional[Union[DirectTarget, RepoRelativeTarget]]:
        return self._targets[0] if self._targets else None

    @public  # type: ignore
    @property
    def job_name(self) -> Optional[str]:
        if len(self._targets) > 1:
            raise DagsterInvalidInvocationError(
                f"Cannot use `job_name` property for sensor {self.name}, which targets multiple jobs."
            )
        return self._targets[0].pipeline_name

    @public  # type: ignore
    @property
    def default_status(self) -> DefaultSensorStatus:
        return self._default_status


@whitelist_for_serdes
class SensorExecutionData(
    NamedTuple(
        "_SensorExecutionData",
        [
            ("run_requests", Optional[Sequence[RunRequest]]),
            ("skip_message", Optional[str]),
            ("cursor", Optional[str]),
            ("pipeline_run_reactions", Optional[Sequence[PipelineRunReaction]]),
        ],
    )
):
    def __new__(
        cls,
        run_requests: Optional[Sequence[RunRequest]] = None,
        skip_message: Optional[str] = None,
        cursor: Optional[str] = None,
        pipeline_run_reactions: Optional[Sequence[PipelineRunReaction]] = None,
    ):
        check.opt_list_param(run_requests, "run_requests", RunRequest)
        check.opt_str_param(skip_message, "skip_message")
        check.opt_str_param(cursor, "cursor")
        check.opt_list_param(pipeline_run_reactions, "pipeline_run_reactions", PipelineRunReaction)
        check.invariant(
            not (run_requests and skip_message), "Found both skip data and run request data"
        )
        return super(SensorExecutionData, cls).__new__(
            cls,
            run_requests=run_requests,
            skip_message=skip_message,
            cursor=cursor,
            pipeline_run_reactions=pipeline_run_reactions,
        )


def wrap_sensor_evaluation(
    sensor_name: str,
    fn: RawSensorEvaluationFunction,
) -> SensorEvaluationFunction:
    def _wrapped_fn(context: SensorEvaluationContext):
        if is_context_provided(fn):
            result = fn(context)
        else:
            result = fn()  # type: ignore

        if inspect.isgenerator(result) or isinstance(result, list):
            for item in result:
                yield item
        elif isinstance(result, (SkipReason, RunRequest)):
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
) -> SensorEvaluationContext:
    """Builds sensor execution context using the provided parameters.

    This function can be used to provide a context to the invocation of a sensor definition.If
    provided, the dagster instance must be persistent; DagsterInstance.ephemeral() will result in an
    error.

    Args:
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A cursor value to provide to the evaluation of the sensor.
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.

    Examples:

        .. code-block:: python

            context = build_sensor_context()
            my_sensor(context)

    """

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    check.opt_str_param(repository_name, "repository_name")
    return SensorEvaluationContext(
        instance_ref=None,
        last_completion_time=None,
        last_run_key=None,
        cursor=cursor,
        repository_name=repository_name,
        instance=instance,
    )


@experimental
def build_multi_asset_sensor_context(
    asset_keys: Sequence[AssetKey],
    repository_def: "RepositoryDefinition",
    instance: Optional[DagsterInstance] = None,
    cursor: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> MultiAssetSensorEvaluationContext:
    """Builds multi asset sensor execution context using the provided parameters.

    This function can be used to provide a context to the invocation of a multi asset sensor definition. If
    provided, the dagster instance must be persistent; DagsterInstance.ephemeral() will result in an
    error.

    Args:
        asset_keys (Sequence[AssetKey]): The list of asset keys monitored by the sensor
        repository_def (RepositoryDefinition): The repository definition that the sensor belongs to.
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A string cursor to provide to the evaluation of the sensor. Must be
            a dictionary of asset key strings to ints that has been converted to a json string
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.

    Examples:

        .. code-block:: python

            with instance_for_test() as instance:
                context = build_multi_asset_sensor_context(asset_keys=[AssetKey("asset_1"), AssetKey("asset_2")], instance=instance)
                my_asset_sensor(context)

    """
    from dagster._core.definitions import RepositoryDefinition

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    check.opt_str_param(repository_name, "repository_name")
    check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)
    return MultiAssetSensorEvaluationContext(
        instance_ref=None,
        last_completion_time=None,
        last_run_key=None,
        cursor=cursor,
        repository_name=repository_name,
        instance=instance,
        asset_keys=asset_keys,
        repository_def=repository_def,
    )


@experimental
def build_asset_sla_sensor_context(
    asset_keys: Sequence[AssetKey],
    repository_def: "RepositoryDefinition",
    instance: Optional[DagsterInstance] = None,
    cursor: Optional[str] = None,
    repository_name: Optional[str] = None,
) -> AssetSLASensorEvaluationContext:
    """Builds asset sla sensor execution context using the provided parameters.

    This function can be used to provide a context to the invocation of an asset sla sensor definition. If
    provided, the dagster instance must be persistent; DagsterInstance.ephemeral() will result in an
    error.

    Args:
        asset_keys (Sequence[AssetKey]): The list of asset keys monitored by the sensor
        repository_def (RepositoryDefinition): The repository definition that the sensor belongs to.
        instance (Optional[DagsterInstance]): The dagster instance configured to run the sensor.
        cursor (Optional[str]): A string cursor to provide to the evaluation of the sensor. Must be
            a dictionary of asset key strings to ints that has been converted to a json string
        repository_name (Optional[str]): The name of the repository that the sensor belongs to.

    Examples:

        .. code-block:: python

            with instance_for_test() as instance:
                context = build_multi_asset_sensor_context(asset_keys=[AssetKey("asset_1"), AssetKey("asset_2")], instance=instance)
                my_asset_sensor(context)

    """
    from dagster._core.definitions import RepositoryDefinition

    check.opt_inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(cursor, "cursor")
    check.opt_str_param(repository_name, "repository_name")
    check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)
    return AssetSLASensorEvaluationContext(
        instance_ref=None,
        last_completion_time=None,
        last_run_key=None,
        cursor=cursor,
        repository_name=repository_name,
        instance=instance,
        asset_keys=asset_keys,
        repository_def=repository_def,
    )


AssetMaterializationFunctionReturn = Union[
    Iterator[Union[RunRequest, SkipReason]], Sequence[RunRequest], RunRequest, SkipReason, None
]
AssetMaterializationFunction = Callable[
    ["SensorEvaluationContext", "EventLogEntry"],
    AssetMaterializationFunctionReturn,
]

MultiAssetMaterializationFunction = Callable[
    ["MultiAssetSensorEvaluationContext"],
    AssetMaterializationFunctionReturn,
]


class AssetSensorDefinition(SensorDefinition):
    """Define an asset sensor that initiates a set of runs based on the materialization of a given
    asset.

    Args:
        name (str): The name of the sensor to create.
        asset_key (AssetKey): The asset_key this sensor monitors.
        asset_materialization_fn (Callable[[SensorEvaluationContext, EventLogEntry], Union[Iterator[Union[RunRequest, SkipReason]], RunRequest, SkipReason]]): The core
            evaluation function for the sensor, which is run at an interval to determine whether a
            run should be launched or not. Takes a :py:class:`~dagster.SensorEvaluationContext` and
            an EventLogEntry corresponding to an AssetMaterialization event.

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
        asset_key: AssetKey,
        job_name: Optional[str],
        asset_materialization_fn: Callable[
            ["SensorExecutionContext", "EventLogEntry"],
            RawSensorEvaluationFunctionReturn,
        ],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)

        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        def _wrap_asset_fn(materialization_fn):
            def _fn(context):
                after_cursor = None
                if context.cursor:
                    try:
                        after_cursor = int(context.cursor)
                    except ValueError:
                        after_cursor = None

                event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=self._asset_key,
                        after_cursor=after_cursor,
                    ),
                    ascending=False,
                    limit=1,
                )

                if not event_records:
                    return

                event_record = event_records[0]
                result = materialization_fn(context, event_record.event_log_entry)
                if inspect.isgenerator(result) or isinstance(result, list):
                    for item in result:
                        yield item
                elif isinstance(result, (SkipReason, RunRequest)):
                    yield result
                context.update_cursor(str(event_record.storage_id))

            return _fn

        super(AssetSensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=job_name,
            evaluation_fn=_wrap_asset_fn(
                check.callable_param(asset_materialization_fn, "asset_materialization_fn"),
            ),
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
        )

    @public  # type: ignore
    @property
    def asset_key(self):
        return self._asset_key


@experimental
class MultiAssetSensorDefinition(SensorDefinition):
    """Define an asset sensor that initiates a set of runs based on the materialization of a list of
    assets.

    Args:
        name (str): The name of the sensor to create.
        asset_keys (Sequence[AssetKey]): The asset_keys this sensor monitors.
        asset_materialization_fn (Callable[[MultiAssetSensorEvaluationContext], Union[Iterator[Union[RunRequest, SkipReason]], RunRequest, SkipReason]]): The core
            evaluation function for the sensor, which is run at an interval to determine whether a
            run should be launched or not. Takes a :py:class:`~dagster.MultiAssetSensorEvaluationContext`.

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
        asset_keys: Sequence[AssetKey],
        job_name: Optional[str],
        asset_materialization_fn: Callable[
            ["MultiAssetSensorEvaluationContext"],
            RawSensorEvaluationFunctionReturn,
        ],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):

        self._asset_keys = check.list_param(asset_keys, "asset_keys", AssetKey)

        def _wrap_asset_fn(materialization_fn):
            def _fn(context):
                context.cursor_has_been_updated = False
                result = materialization_fn(context)
                if result is None:
                    return

                # because the materialization_fn can yield results (see _wrapped_fn in multi_asset_sensor decorator),
                # even if you return None in a sensor, it will still cause in inspect.isgenerator(result) == True.
                # So keep track to see if we actually return any values and should update the cursor
                runs_yielded = False
                if inspect.isgenerator(result) or isinstance(result, list):
                    for item in result:
                        runs_yielded = True
                        yield item
                elif isinstance(result, RunRequest):
                    runs_yielded = True
                    yield result
                elif isinstance(result, SkipReason):
                    # if result is a SkipReason, we don't update the cursor, so don't set runs_yielded = True
                    yield result

                if runs_yielded and not context.cursor_has_been_updated:
                    raise DagsterInvalidDefinitionError(
                        "Asset materializations have been handled in this sensor, "
                        "but the cursor was not updated. This means the same materialization events "
                        "will be handled in the next sensor tick. Use context.advance_cursor or "
                        "context.advance_all_cursors to update the cursor."
                    )

            return _fn

        super(MultiAssetSensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=job_name,
            evaluation_fn=_wrap_asset_fn(
                check.callable_param(asset_materialization_fn, "asset_materialization_fn"),
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
                    args[0], context_param_name, MultiAssetSensorEvaluationContext
                )
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.inst_param(
                    kwargs[context_param_name],
                    context_param_name,
                    MultiAssetSensorEvaluationContext,
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
    def asset_keys(self):
        return self._asset_keys


@experimental
class AssetSLASensorDefinition(SensorDefinition):
    """Define a sensor that can initiate a set of runs or alerts when an asset stops passing its defined SLA.

    Args:
        name (str): The name of the sensor to create.
        asset_keys (Sequence[AssetKey]): The asset_keys this sensor monitors.
        asset_materialization_fn (Callable[[MultiAssetSensorEvaluationContext], Union[Iterator[Union[RunRequest, SkipReason]], RunRequest, SkipReason]]): The core
            evaluation function for the sensor, which is run at an interval to determine whether a
            run should be launched or not. Takes a :py:class:`~dagster.MultiAssetSensorEvaluationContext`.

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
        job_name: Optional[str],
        asset_materialization_fn: Callable[
            ["MultiAssetSensorEvaluationContext"],
            RawSensorEvaluationFunctionReturn,
        ],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):

        self._asset_keys = check.opt_nullable_sequence_param(asset_keys, "asset_keys", AssetKey)

        def _wrap_asset_fn(materialization_fn):
            def _fn(context):
                context.cursor_has_been_updated = False
                result = materialization_fn(context)
                if result is None:
                    return

                if inspect.isgenerator(result) or isinstance(result, list):
                    for item in result:
                        yield item
                elif isinstance(result, RunRequest):
                    yield result
                elif isinstance(result, SkipReason):
                    # if result is a SkipReason, we don't update the cursor, so don't set runs_yielded = True
                    yield result

                context.update_cursor(context.next_cursor)

            return _fn

        super(AssetSLASensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=job_name,
            evaluation_fn=_wrap_asset_fn(
                check.callable_param(asset_materialization_fn, "asset_materialization_fn"),
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
                    args[0], context_param_name, AssetSLASensorEvaluationContext
                )
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.inst_param(
                    kwargs[context_param_name],
                    context_param_name,
                    AssetSLASensorEvaluationContext,
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
    def asset_keys(self):
        return self._asset_keys
