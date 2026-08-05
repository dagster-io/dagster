import json
import os
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import contextmanager
from datetime import timezone
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, cast  # noqa: UP035
from uuid import uuid4

import dagster._check as check
from dagster import AssetCheckKey, DagsterInvalidInvocationError, PartitionsDefinition
from dagster._core.assets import AssetDetails
from dagster._core.definitions.events import AssetKey, ExpectationResult
from dagster._core.definitions.freshness import FreshnessStateRecord
from dagster._core.event_api import (
    AssetRecordsFilter,
    EventLogRecord,
    EventRecordsFilter,
    EventRecordsResult,
    PartitionKeyFilter,
    RunShardedEventsCursor,
    RunStatusChangeRecordsFilter,
)
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.stats import RunStepKeyStatsSnapshot, RunStepMarker, StepEventStatus
from dagster._core.instance.config import PoolConfig, PoolGranularity
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckPartitionInfo,
)
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
from dagster._core.storage.event_log.base import (
    AssetCheckSummaryRecord,
    AssetEntry,
    AssetRecord,
    EventLogConnection,
    EventLogStorage,
    PlannedMaterializationInfo,
    PoolLimit,
)
from dagster._core.storage.partition_status_cache import AssetStatusCacheValue
from dagster._core.types.pagination import PaginatedResults
from dagster._serdes import ConfigurableClass, ConfigurableClassData, serialize_value
from dagster._time import datetime_from_timestamp
from dagster._utils.concurrency import (
    ClaimedSlotInfo,
    ConcurrencyClaimStatus,
    ConcurrencyKeyInfo,
    ConcurrencySlotStatus,
    PendingStepInfo,
)
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.merger import merge_dicts
from dagster_cloud_cli.core.errors import DagsterCloudAgentServerError
from dagster_shared.serdes.serdes import deserialize_value
from typing_extensions import Self

from dagster_cloud.api.dagster_cloud_api import StoreEventBatchRequest
from dagster_cloud.metrics.tracer import Tracer
from dagster_cloud.storage.event_logs.utils import truncate_event
from dagster_cloud.util import compressed_namedtuple_upload_file

if TYPE_CHECKING:
    from dagster_cloud.instance import DagsterCloudAgentInstance


# Guard against out of order event insertion issues by default
DEFAULT_RUN_SCOPED_EVENT_TAILER_OFFSET = 20000


from dagster_cloud.storage.event_logs.queries import (
    ADD_DYNAMIC_PARTITIONS_MUTATION,
    CHECK_CONCURRENCY_CLAIM_QUERY,
    CLAIM_CONCURRENCY_SLOT_MUTATION,
    DELETE_CONCURRENCY_LIMIT_MUTATION,
    DELETE_DYNAMIC_PARTITION_MUTATION,
    DELETE_EVENTS_MUTATION,
    ENABLE_SECONDARY_INDEX_MUTATION,
    FETCH_FAILED_MATERIALIZATIONS_QUERY,
    FETCH_MATERIALIZATIONS_QUERY,
    FETCH_OBSERVATIONS_QUERY,
    FETCH_PLANNED_MATERIALIZATIONS,
    FREE_CONCURRENCY_SLOT_FOR_STEP_MUTATION,
    FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION,
    GET_ALL_ASSET_KEYS_QUERY,
    GET_ASSET_CHECK_STATE_QUERY,
    GET_ASSET_RECORDS_QUERY,
    GET_ASSET_STATUS_CACHE_VALUES,
    GET_CONCURRENCY_INFO_QUERY,
    GET_CONCURRENCY_KEYS_QUERY,
    GET_DYNAMIC_PARTITIONS_QUERY,
    GET_EVENT_RECORDS_QUERY,
    GET_EVENT_TAGS_FOR_ASSET,
    GET_LATEST_ASSET_CHECK_EXECUTION_BY_KEY_QUERY,
    GET_LATEST_ASSET_PARTITION_MATERIALIZATION_ATTEMPTS_WITHOUT_MATERIALIZATIONS,
    GET_LATEST_MATERIALIZATION_EVENTS_QUERY,
    GET_LATEST_PLANNED_MATERIALIZATION_INFO,
    GET_LATEST_STORAGE_ID_BY_PARTITION,
    GET_LATEST_TAGS_BY_PARTITION,
    GET_MATERIALIZATION_COUNT_BY_PARTITION,
    GET_MATERIALIZED_PARTITIONS,
    GET_MAXIMUM_RECORD_ID,
    GET_PAGINATED_DYNAMIC_PARTITIONS_QUERY,
    GET_POOL_CONFIG_QUERY,
    GET_POOL_LIMITS_QUERY,
    GET_RECORDS_FOR_RUN_QUERY,
    GET_RUN_STATUS_CHANGE_EVENTS_QUERY,
    GET_STATS_FOR_RUN_QUERY,
    GET_STEP_STATS_FOR_RUN_QUERY,
    GET_UPDATED_DATA_VERSION_PARTITIONS,
    HAS_ASSET_KEY_QUERY,
    HAS_DYNAMIC_PARTITION_QUERY,
    INITIALIZE_CONCURRENCY_LIMIT_MUTATION,
    IS_ASSET_AWARE_QUERY,
    IS_PERSISTENT_QUERY,
    REINDEX_MUTATION,
    SET_CONCURRENCY_SLOTS_MUTATION,
    STORE_EVENT_BATCH_MUTATION,
    STORE_EVENT_MUTATION,
    UPGRADE_EVENT_LOG_STORAGE_MUTATION,
    WIPE_ASSET_CACHED_STATUS_DATA_MUTATION,
    WIPE_ASSET_MUTATION,
    WIPE_ASSET_PARTITIONS_MUTATION,
    WIPE_EVENT_LOG_STORAGE_MUTATION,
)


def _input_for_event(event: EventLogEntry):
    return {
        "errorInfo": _input_for_serializable_error_info(event.error_info),
        "level": event.level,
        "userMessage": event.user_message,
        "runId": event.run_id,
        "timestamp": event.timestamp,
        "stepKey": event.step_key,
        "pipelineName": event.job_name,
        "dagsterEvent": _input_for_dagster_event(event.dagster_event),
    }


def _input_for_serializable_error_info(serializable_error_info: SerializableErrorInfo | None):
    check.opt_inst_param(serializable_error_info, "serializable_error_info", SerializableErrorInfo)

    if serializable_error_info is None:
        return None

    return {
        "message": serializable_error_info.message,
        "stack": serializable_error_info.stack,
        "clsName": serializable_error_info.cls_name,
        "cause": _input_for_serializable_error_info(serializable_error_info.cause),
    }


def _input_for_dagster_event(dagster_event: DagsterEvent | None):
    if dagster_event is None:
        return None

    return {
        "eventTypeValue": dagster_event.event_type_value,
        "pipelineName": dagster_event.job_name,
        "stepHandleKey": dagster_event.step_handle.to_key() if dagster_event.step_handle else None,
        "solidHandleId": (str(dagster_event.node_handle) if dagster_event.node_handle else None),
        "stepKindValue": dagster_event.step_kind_value,
        "loggingTags": (
            json.dumps(dagster_event.logging_tags) if dagster_event.logging_tags else None
        ),
        "eventSpecificData": (
            serialize_value(dagster_event.event_specific_data)
            if dagster_event.event_specific_data
            else None
        ),
        "message": dagster_event.message,
        "pid": dagster_event.pid,
        "stepKey": dagster_event.step_key,
    }


def _event_log_entry_from_graphql(graphene_event_log_entry: dict) -> EventLogEntry:
    check.dict_param(graphene_event_log_entry, "graphene_event_log_entry")

    return EventLogEntry(
        error_info=(
            deserialize_value(
                check.str_elem(graphene_event_log_entry, "errorInfo"), SerializableErrorInfo
            )
            if graphene_event_log_entry.get("errorInfo") is not None
            else None
        ),
        level=check.int_elem(graphene_event_log_entry, "level"),
        user_message=check.str_elem(graphene_event_log_entry, "userMessage"),
        run_id=check.str_elem(graphene_event_log_entry, "runId"),
        timestamp=check.float_elem(graphene_event_log_entry, "timestamp"),
        step_key=check.opt_str_elem(graphene_event_log_entry, "stepKey"),
        job_name=check.opt_str_elem(graphene_event_log_entry, "pipelineName"),
        dagster_event=(
            deserialize_value(
                check.str_elem(graphene_event_log_entry, "dagsterEvent"),
                DagsterEvent,
            )
            if graphene_event_log_entry.get("dagsterEvent") is not None
            else None
        ),
    )


def _get_event_records_filter_input(
    event_records_filter,
) -> dict[str, Any] | None:
    check.opt_inst_param(event_records_filter, "event_records_filter", EventRecordsFilter)

    if event_records_filter is None:
        return None

    run_updated_timestamp = None
    if isinstance(event_records_filter.after_cursor, RunShardedEventsCursor):
        # we should parse this correctly, even if this is a vestigial field that only has semantic
        # meaning in the context of a run-sharded cursor against a SQLite backed event-log
        updated_dt = event_records_filter.after_cursor.run_updated_after
        updated_dt = updated_dt if updated_dt.tzinfo else updated_dt.replace(tzinfo=timezone.utc)
        run_updated_timestamp = updated_dt.timestamp()

    return {
        "eventType": (
            event_records_filter.event_type.value if event_records_filter.event_type else None
        ),
        "assetKey": (
            event_records_filter.asset_key.to_string() if event_records_filter.asset_key else None
        ),
        "assetPartitions": event_records_filter.asset_partitions,
        "afterTimestamp": event_records_filter.after_timestamp,
        "beforeTimestamp": event_records_filter.before_timestamp,
        "beforeCursor": (
            event_records_filter.before_cursor.id
            if isinstance(event_records_filter.before_cursor, RunShardedEventsCursor)
            else event_records_filter.before_cursor
        ),
        "afterCursor": (
            event_records_filter.after_cursor.id
            if isinstance(event_records_filter.after_cursor, RunShardedEventsCursor)
            else event_records_filter.after_cursor
        ),
        "runUpdatedAfter": run_updated_timestamp,
        "tags": (
            [
                merge_dicts(
                    {"key": tag_key},
                    ({"value": tag_value} if isinstance(tag_value, str) else {"values": tag_value}),
                )
                for tag_key, tag_value in event_records_filter.tags.items()
            ]
            if event_records_filter.tags
            else None
        ),
        "storageIds": event_records_filter.storage_ids,
    }


def _get_asset_records_filter_input(
    records_filter: AssetKey | AssetRecordsFilter,
) -> dict[str, Any]:
    check.opt_inst_param(records_filter, "records_filter", (AssetKey, AssetRecordsFilter))

    if isinstance(records_filter, AssetKey):
        return {"assetKey": records_filter.to_string()}

    return {
        "assetKey": records_filter.asset_key.to_string() if records_filter.asset_key else None,
        "assetPartitions": records_filter.asset_partitions,
        "afterTimestamp": records_filter.after_timestamp,
        "beforeTimestamp": records_filter.before_timestamp,
        "afterStorageId": records_filter.after_storage_id,
        "beforeStorageId": records_filter.before_storage_id,
        "tags": (
            [
                merge_dicts(
                    {"key": tag_key},
                    ({"value": tag_value} if isinstance(tag_value, str) else {"values": tag_value}),
                )
                for tag_key, tag_value in records_filter.tags.items()
            ]
            if records_filter.tags
            else None
        ),
        "storageIds": records_filter.storage_ids,
    }


def _fetch_run_status_changes_filter_input(records_filter) -> dict[str, Any]:
    check.inst_param(
        records_filter, "records_filter", (DagsterEventType, RunStatusChangeRecordsFilter)
    )

    if isinstance(records_filter, DagsterEventType):
        return {"eventType": records_filter.value}

    return {
        "eventType": records_filter.event_type.value if records_filter.event_type else None,
        "afterTimestamp": records_filter.after_timestamp,
        "beforeTimestamp": records_filter.before_timestamp,
        "afterStorageId": records_filter.after_storage_id,
        "beforeStorageId": records_filter.before_storage_id,
        "storageIds": records_filter.storage_ids,
        "jobNames": records_filter.job_names,
    }


def _event_record_from_graphql(graphene_event_record: dict) -> EventLogRecord:
    check.dict_param(graphene_event_record, "graphene_event_record")

    return EventLogRecord(
        storage_id=check.int_elem(graphene_event_record, "storageId"),
        event_log_entry=_event_log_entry_from_graphql(graphene_event_record["eventLogEntry"]),
    )


def _asset_entry_from_graphql(graphene_asset_entry: dict) -> AssetEntry:
    check.dict_param(graphene_asset_entry, "graphene_asset_entry")
    return AssetEntry(
        asset_key=AssetKey(graphene_asset_entry["assetKey"]["path"]),
        last_materialization_record=(
            _event_record_from_graphql(graphene_asset_entry["lastMaterializationRecord"])
            if graphene_asset_entry["lastMaterializationRecord"]
            else None
        ),
        last_run_id=graphene_asset_entry["lastRunId"],
        asset_details=(
            AssetDetails(
                last_wipe_timestamp=graphene_asset_entry["assetDetails"]["lastWipeTimestamp"]
            )
            if graphene_asset_entry["assetDetails"]
            else None
        ),
        cached_status=(
            AssetStatusCacheValue(
                latest_storage_id=graphene_asset_entry["cachedStatus"]["latestStorageId"],
                partitions_def_id=graphene_asset_entry["cachedStatus"]["partitionsDefId"],
                serialized_materialized_partition_subset=graphene_asset_entry["cachedStatus"][
                    "serializedMaterializedPartitionSubset"
                ],
                serialized_failed_partition_subset=graphene_asset_entry["cachedStatus"][
                    "serializedFailedPartitionSubset"
                ],
                serialized_in_progress_partition_subset=graphene_asset_entry["cachedStatus"][
                    "serializedInProgressPartitionSubset"
                ],
                earliest_in_progress_materialization_event_id=graphene_asset_entry["cachedStatus"][
                    "earliestInProgressMaterializationEventId"
                ],
            )
            if graphene_asset_entry["cachedStatus"]
            else None
        ),
        last_observation_record=(
            _event_record_from_graphql(graphene_asset_entry["lastObservationRecord"])
            if graphene_asset_entry["lastObservationRecord"]
            else None
        ),
        last_planned_materialization_storage_id=graphene_asset_entry[
            "lastPlannedMaterializationStorageId"
        ],
        last_planned_materialization_run_id=graphene_asset_entry["lastPlannedMaterializationRunId"],
    )


def _asset_record_from_graphql(graphene_asset_record: dict) -> AssetRecord:
    check.dict_param(graphene_asset_record, "graphene_asset_record")
    return AssetRecord(
        storage_id=graphene_asset_record["storageId"],
        asset_entry=_asset_entry_from_graphql(graphene_asset_record["assetEntry"]),
    )


def _asset_check_execution_record_from_graphql(data: dict, key: AssetCheckKey):
    return AssetCheckExecutionRecord(
        key=key,
        id=data["id"],
        run_id=data["runId"],
        status=AssetCheckExecutionRecordStatus(data["status"]),
        event=_event_log_entry_from_graphql(data["event"]),
        create_timestamp=data["createTimestamp"],
        partition=data.get("partition"),
    )


def _asset_check_summary_record_from_graphql(
    graphene_asset_check_summary_record: dict,
) -> AssetCheckSummaryRecord:
    check.dict_param(graphene_asset_check_summary_record, "graphene_asset_check_summary_record")

    asset_check_key = AssetCheckKey.from_graphql_input(
        graphene_asset_check_summary_record["assetCheckKey"]
    )
    return AssetCheckSummaryRecord(
        asset_check_key=asset_check_key,
        last_check_execution_record=(
            _asset_check_execution_record_from_graphql(
                graphene_asset_check_summary_record["lastCheckExecutionRecord"],
                asset_check_key,
            )
            if graphene_asset_check_summary_record["lastCheckExecutionRecord"]
            else None
        ),
        last_completed_check_execution_record=(
            _asset_check_execution_record_from_graphql(
                graphene_asset_check_summary_record["lastCompletedCheckExecutionRecord"],
                asset_check_key,
            )
            if graphene_asset_check_summary_record["lastCompletedCheckExecutionRecord"]
            else None
        ),
        last_run_id=graphene_asset_check_summary_record["lastRunId"],
    )


def _event_records_result_from_graphql(graphene_event_records_result: dict) -> EventRecordsResult:
    return EventRecordsResult(
        records=[
            _event_record_from_graphql(record)
            for record in graphene_event_records_result["records"]
        ],
        cursor=graphene_event_records_result["cursor"],
        has_more=graphene_event_records_result["hasMore"],
    )


def _claimed_slot_from_graphql(graphene_claimed_slot_dict: dict) -> ClaimedSlotInfo:
    check.dict_param(graphene_claimed_slot_dict, "graphene_claimed_slot_dict")
    return ClaimedSlotInfo(
        run_id=graphene_claimed_slot_dict["runId"],
        step_key=graphene_claimed_slot_dict["stepKey"],
    )


def _pending_step_from_graphql(graphene_pending_step: dict) -> PendingStepInfo:
    check.dict_param(graphene_pending_step, "graphene_pending_step")
    return PendingStepInfo(
        run_id=graphene_pending_step["runId"],
        step_key=graphene_pending_step["stepKey"],
        enqueued_timestamp=datetime_from_timestamp(graphene_pending_step["enqueuedTimestamp"]),
        assigned_timestamp=(
            datetime_from_timestamp(graphene_pending_step["assignedTimestamp"])
            if graphene_pending_step["assignedTimestamp"]
            else None
        ),
        priority=graphene_pending_step["priority"],
    )


class GraphQLEventLogStorage(EventLogStorage, ConfigurableClass):
    def __init__(self, inst_data=None, override_graphql_client=None):
        """Initialize this class directly only for test. Use the ConfigurableClass machinery to
        init from instance yaml.
        """
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._override_graphql_client = override_graphql_client
        self._tracer = Tracer()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(inst_data=inst_data)

    @property
    def _graphql_client(self):
        return (
            self._override_graphql_client
            if self._override_graphql_client
            else self._instance.graphql_client  # ty: ignore[unresolved-attribute]
        )

    @property
    def agent_instance(self) -> "DagsterCloudAgentInstance":
        return cast("DagsterCloudAgentInstance", self._instance)

    def _execute_query(self, query, variables=None, headers=None, idempotent_mutation=False):
        return self._graphql_client.execute(
            query,
            variable_values=variables,
            headers=headers,
            idempotent_mutation=idempotent_mutation,
        )

    def get_maximum_record_id(self) -> int | None:
        res = self._execute_query(GET_MAXIMUM_RECORD_ID)
        return res["data"]["eventLogs"]["getMaximumRecordId"]

    def get_records_for_run(
        self,
        run_id: str,
        cursor: str | None = None,
        of_type: DagsterEventType | set[DagsterEventType] | None = None,
        limit: int | None = None,
        ascending: bool = True,
    ) -> EventLogConnection:
        check.invariant(not of_type or isinstance(of_type, (DagsterEventType, frozenset, set)))

        is_of_type_set = isinstance(of_type, (set, frozenset))

        res = self._execute_query(
            GET_RECORDS_FOR_RUN_QUERY,
            variables={
                "runId": check.str_param(run_id, "run_id"),
                "cursor": check.opt_str_param(cursor, "cursor"),
                "ofType": (
                    cast("DagsterEventType", of_type).value
                    if of_type and not is_of_type_set
                    else None
                ),
                "ofTypes": (
                    [dagster_type.value for dagster_type in cast("set", of_type)]
                    if of_type and is_of_type_set
                    else None
                ),
                "limit": limit,
                # only send False for back-compat since True is the default
                **({"ascending": False} if not ascending else {}),
            },
        )
        connection_data = res["data"]["eventLogs"]["getRecordsForRun"]
        return EventLogConnection(
            records=[_event_record_from_graphql(record) for record in connection_data["records"]],
            cursor=connection_data["cursor"],
            has_more=connection_data["hasMore"],
        )

    def get_stats_for_run(self, run_id: str) -> DagsterRunStatsSnapshot:
        res = self._execute_query(
            GET_STATS_FOR_RUN_QUERY, variables={"runId": check.str_param(run_id, "run_id")}
        )
        stats = res["data"]["eventLogs"]["getStatsForRun"]
        return DagsterRunStatsSnapshot(
            run_id=check.str_elem(stats, "runId"),
            steps_succeeded=check.int_elem(stats, "stepsSucceeded"),
            steps_failed=check.int_elem(stats, "stepsFailed"),
            materializations=check.int_elem(stats, "materializations"),
            expectations=check.int_elem(stats, "expectations"),
            enqueued_time=check.opt_float_elem(stats, "enqueuedTime"),
            launch_time=check.opt_float_elem(stats, "launchTime"),
            start_time=check.opt_float_elem(stats, "startTime"),
            end_time=check.opt_float_elem(stats, "endTime"),
        )

    def get_step_stats_for_run(  # ty: ignore[invalid-method-override], fix me!
        self, run_id: str, step_keys: list[str] | None = None
    ) -> list[RunStepKeyStatsSnapshot]:
        res = self._execute_query(
            GET_STEP_STATS_FOR_RUN_QUERY,
            variables={
                "runId": check.str_param(run_id, "run_id"),
                "stepKeys": check.opt_list_param(step_keys, "step_keys", of_type=str),
            },
        )
        step_stats = res["data"]["eventLogs"]["getStepStatsForRun"]
        return [
            RunStepKeyStatsSnapshot(
                run_id=check.str_elem(stats, "runId"),
                step_key=check.str_elem(stats, "stepKey"),
                status=(
                    getattr(StepEventStatus, check.str_elem(stats, "status"))
                    if stats.get("status") is not None
                    else None
                ),
                start_time=check.opt_float_elem(stats, "startTime"),
                end_time=check.opt_float_elem(stats, "endTime"),
                materialization_events=[
                    deserialize_value(materialization_event, EventLogEntry)
                    for materialization_event in check.opt_list_elem(
                        stats, "materializationEvents", of_type=str
                    )
                ],
                expectation_results=[
                    deserialize_value(expectation_result, ExpectationResult)
                    for expectation_result in check.opt_list_elem(
                        stats, "expectationResults", of_type=str
                    )
                ],
                attempts=check.opt_int_elem(stats, "attempts"),
                attempts_list=[
                    deserialize_value(marker, RunStepMarker)
                    for marker in check.opt_list_elem(stats, "attemptsList", of_type=str)
                ],
                markers=[
                    deserialize_value(marker, RunStepMarker)
                    for marker in check.opt_list_elem(stats, "markers", of_type=str)
                ],
            )
            for stats in step_stats
        ]

    def _store_events_http(self, headers, events: Sequence[EventLogEntry]):
        batch_request = StoreEventBatchRequest(event_log_entries=events)
        with compressed_namedtuple_upload_file(batch_request) as f:
            self.agent_instance.http_client.post(
                url=self.agent_instance.dagster_cloud_store_events_url,
                headers=headers,
                files={"store_events.tmp": f},
            )

    def _add_metric_header(self, headers: dict[str, str]):
        if os.getenv("DISABLE_DAGSTER_CLOUD_STORE_EVENT_SEND_METRICS") is not None:
            return

        try:
            span_metric = self._tracer.pop_serialized_span()
            if span_metric:
                headers["Dagster-Cloud-Metric"] = span_metric
        except:
            pass

    @contextmanager
    def _event_span(self, event: EventLogEntry):
        if os.getenv("DISABLE_DAGSTER_CLOUD_STORE_EVENT_SEND_METRICS") is not None:
            yield
        else:
            with self._tracer.start_span("store-event") as event_span:
                event_span.set_attribute(
                    "event_type",
                    event.dagster_event.event_type_value
                    if event.dagster_event is not None
                    else "user",
                )
                event_span.set_attribute("run_id", event.run_id)
                yield

    def store_event(self, event: EventLogEntry):
        check.inst_param(event, "event", EventLogEntry)
        headers = {"Idempotency-Key": str(uuid4()), "X-Event-Write": "true"}

        self._add_metric_header(headers)

        event = truncate_event(event)

        with self._event_span(event):
            if os.getenv("DAGSTER_CLOUD_STORE_EVENT_OVER_HTTP"):
                self._store_events_http(headers, [event])
            else:
                self._execute_query(
                    STORE_EVENT_MUTATION,
                    variables={
                        "eventRecord": _input_for_event(event),
                    },
                    headers=headers,
                )

    def store_event_batch(self, events: Sequence[EventLogEntry]):
        check.sequence_param(events, "events", of_type=EventLogEntry)
        headers = {"Idempotency-Key": str(uuid4()), "X-Event-Write": "true"}

        if os.getenv("DAGSTER_CLOUD_STORE_EVENT_OVER_HTTP"):
            self._store_events_http(headers, events)
        else:
            self._execute_query(
                STORE_EVENT_BATCH_MUTATION,
                variables={
                    "eventRecords": [_input_for_event(event) for event in events],
                },
                headers=headers,
            )

    def delete_events(self, run_id: str):
        self._execute_query(
            DELETE_EVENTS_MUTATION, variables={"runId": check.str_param(run_id, "run_id")}
        )
        return

    def upgrade(self):
        return self._execute_query(UPGRADE_EVENT_LOG_STORAGE_MUTATION)

    def reindex_assets(self, print_fn: Callable | None = lambda _: None, force: bool = False):
        return self._execute_query(
            REINDEX_MUTATION, variables={"force": check.bool_param(force, "force")}
        )

    def reindex_events(self, print_fn: Callable | None = lambda _: None, force: bool = False):
        return self._execute_query(
            REINDEX_MUTATION, variables={"force": check.bool_param(force, "force")}
        )

    def wipe(self):
        return self._execute_query(WIPE_EVENT_LOG_STORAGE_MUTATION)

    def watch(self, run_id: str, cursor: str, callback: Callable):  # ty: ignore[invalid-method-override], fix me!
        raise NotImplementedError("Not callable from user cloud")

    def end_watch(self, run_id: str, handler: Callable):
        raise NotImplementedError("Not callable from user cloud")

    def enable_secondary_index(self, name: str, run_id: str | None = None):
        return self._execute_query(
            ENABLE_SECONDARY_INDEX_MUTATION,
            variables={
                "name": check.str_param(name, "name"),
                "runId": check.str_param(run_id, "run_id"),
            },
        )

    @property
    def is_persistent(self) -> bool:
        res = self._execute_query(IS_PERSISTENT_QUERY)
        return res["data"]["eventLogs"]["isPersistent"]

    @property
    def is_asset_aware(self) -> bool:
        res = self._execute_query(IS_ASSET_AWARE_QUERY)
        return res["data"]["eventLogs"]["isAssetAware"]

    def get_event_records(
        self,
        event_records_filter: EventRecordsFilter | None = None,
        limit: int | None = None,
        ascending: bool | None = False,
    ) -> Sequence[EventLogRecord]:
        check.opt_inst_param(event_records_filter, "event_records_filter", EventRecordsFilter)
        check.opt_int_param(limit, "limit")
        check.bool_param(ascending, "ascending")

        res = self._execute_query(
            GET_EVENT_RECORDS_QUERY,
            variables={
                "eventRecordsFilter": _get_event_records_filter_input(event_records_filter),
                "limit": limit,
                "ascending": ascending,
            },
        )
        return [
            _event_record_from_graphql(result)
            for result in res["data"]["eventLogs"]["getEventRecords"]
        ]

    @property
    def asset_records_have_last_observation(self) -> bool:
        return True

    @property
    def supports_partition_subset_in_asset_materialization_planned_events(self) -> bool:
        return True

    @property
    def asset_records_have_last_planned_and_failed_materializations(self) -> bool:
        return True

    @property
    def can_store_asset_failure_events(self) -> bool:
        return True

    def get_asset_check_summary_records(
        self, asset_check_keys: Sequence[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckSummaryRecord]:
        res = self._execute_query(
            GET_ASSET_CHECK_STATE_QUERY,
            variables={"assetCheckKeys": [key.to_user_string() for key in asset_check_keys]},
        )
        records = {}
        for result in res["data"]["eventLogs"]["getAssetCheckSummaryRecord"]:
            record = _asset_check_summary_record_from_graphql(result)
            check_key = AssetCheckKey.from_graphql_input(result["assetCheckKey"])
            records[check_key] = record
        return records

    def get_asset_records(
        self, asset_keys: Sequence[AssetKey] | None = None
    ) -> Sequence[AssetRecord]:
        res = self._execute_query(
            GET_ASSET_RECORDS_QUERY,
            variables={
                "assetKeys": (
                    [asset_key.to_string() for asset_key in asset_keys] if asset_keys else []
                )
            },
        )

        return [
            _asset_record_from_graphql(result)
            for result in res["data"]["eventLogs"]["getAssetRecords"]
        ]

    def get_freshness_state_records(
        self, keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, FreshnessStateRecord]:
        raise NotImplementedError("Not callable from user cloud")

    def has_asset_key(self, asset_key: AssetKey):
        check.inst_param(asset_key, "asset_key", AssetKey)

        res = self._execute_query(
            HAS_ASSET_KEY_QUERY, variables={"assetKey": asset_key.to_string()}
        )
        return res["data"]["eventLogs"]["hasAssetKey"]

    def all_asset_keys(self) -> Iterable[AssetKey]:  # ty: ignore[invalid-method-override], fix me!
        res = self._execute_query(GET_ALL_ASSET_KEYS_QUERY)
        return [
            check.not_none(AssetKey.from_db_string(asset_key_string))
            for asset_key_string in res["data"]["eventLogs"]["getAllAssetKeys"]
        ]

    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, EventLogEntry | None]:
        check.iterable_param(asset_keys, "asset_keys", AssetKey)

        res = self._execute_query(
            GET_LATEST_MATERIALIZATION_EVENTS_QUERY,
            variables={"assetKeys": [asset_key.to_string() for asset_key in asset_keys]},
        )

        result = {}
        for entry in res["data"]["eventLogs"]["getLatestMaterializationEvents"]:
            event = _event_log_entry_from_graphql(entry)
            if event.dagster_event and event.dagster_event.asset_key is not None:
                result[event.dagster_event.asset_key] = event

        return result

    def can_read_asset_status_cache(self) -> bool:
        # cached_status_data column exists in the asset_key table
        return True

    def can_write_asset_status_cache(self) -> bool:
        return False

    def update_asset_cached_status_data(
        self, asset_key: AssetKey, cache_values: AssetStatusCacheValue
    ) -> None:
        raise NotImplementedError("Not callable from user cloud")

    def wipe_asset_cached_status(self, asset_key: AssetKey) -> None:
        res = self._execute_query(
            WIPE_ASSET_CACHED_STATUS_DATA_MUTATION, variables={"assetKey": asset_key.to_string()}
        )
        return res

    def get_materialized_partitions(
        self,
        asset_key: AssetKey,
        before_cursor: int | None = None,
        after_cursor: int | None = None,
    ) -> set[str]:
        check.inst_param(asset_key, "asset_key", AssetKey)
        check.opt_int_param(before_cursor, "before_cursor")
        check.opt_int_param(after_cursor, "after_cursor")
        res = self._execute_query(
            GET_MATERIALIZED_PARTITIONS,
            variables={
                "assetKey": asset_key.to_string(),
                "beforeCursor": before_cursor,
                "afterCursor": after_cursor,
            },
        )
        materialized_partitions = res["data"]["eventLogs"]["getMaterializedPartitions"]
        return set(materialized_partitions)

    def get_materialization_count_by_partition(
        self,
        asset_keys: Sequence[AssetKey],
        after_cursor: int | None = None,
    ) -> Mapping[AssetKey, Mapping[str, int]]:
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        check.opt_int_param(after_cursor, "after_cursor")

        res = self._execute_query(
            GET_MATERIALIZATION_COUNT_BY_PARTITION,
            variables={
                "assetKeys": [asset_key.to_string() for asset_key in asset_keys],
                "afterCursor": after_cursor,
            },
        )

        materialization_count_result = res["data"]["eventLogs"][
            "getMaterializationCountByPartition"
        ]

        materialization_count_by_partition: dict[AssetKey, dict[str, int]] = {
            asset_key: {} for asset_key in asset_keys
        }
        for asset_count in materialization_count_result:
            asset_key = check.not_none(AssetKey.from_db_string(asset_count["assetKey"]))
            for graphene_partition_count in asset_count["materializationCountByPartition"]:
                materialization_count_by_partition[asset_key][
                    graphene_partition_count["partition"]
                ] = graphene_partition_count["materializationCount"]

        return materialization_count_by_partition

    def get_latest_storage_id_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        partitions: set[str] | None = None,
    ) -> Mapping[str, int]:
        res = self._execute_query(
            GET_LATEST_STORAGE_ID_BY_PARTITION,
            variables={
                "assetKey": asset_key.to_string(),
                "eventType": event_type.value,
                "partitions": list(partitions) if partitions else None,
            },
        )
        latest_storage_id_result = res["data"]["eventLogs"]["getLatestStorageIdByPartition"]
        latest_storage_id_by_partition: dict[str, int] = {}

        for graphene_latest_storage_id in latest_storage_id_result:
            latest_storage_id_by_partition[graphene_latest_storage_id["partition"]] = (
                graphene_latest_storage_id["storageId"]
            )

        return latest_storage_id_by_partition

    def get_latest_tags_by_partition(
        self,
        asset_key: AssetKey,
        event_type: DagsterEventType,
        tag_keys: Sequence[str] | None = None,
        asset_partitions: Sequence[str] | None = None,
        before_cursor: int | None = None,
        after_cursor: int | None = None,
    ) -> Mapping[str, Mapping[str, str]]:
        res = self._execute_query(
            GET_LATEST_TAGS_BY_PARTITION,
            variables={
                "assetKey": asset_key.to_string(),
                "eventType": event_type.value,
                "tagKeys": tag_keys,
                "assetPartitions": asset_partitions,
                "beforeCursor": before_cursor,
                "afterCursor": after_cursor,
            },
        )
        latest_tags_by_partition_result = res["data"]["eventLogs"]["getLatestTagsByPartition"]
        latest_tags_by_partition: dict[str, dict[str, str]] = defaultdict(dict)
        for tag_by_partition in latest_tags_by_partition_result:
            latest_tags_by_partition[tag_by_partition["partition"]][tag_by_partition["key"]] = (
                tag_by_partition["value"]
            )

        # convert defaultdict to dict
        return dict(latest_tags_by_partition)

    def get_latest_asset_partition_materialization_attempts_without_materializations(
        self, asset_key: AssetKey, after_storage_id: int | None = None
    ) -> Mapping[str, tuple[str, int]]:
        res = self._execute_query(
            GET_LATEST_ASSET_PARTITION_MATERIALIZATION_ATTEMPTS_WITHOUT_MATERIALIZATIONS,
            variables={
                "assetKey": asset_key.to_string(),
                "afterStorageId": after_storage_id,
            },
        )
        result = res["data"]["eventLogs"][
            "getLatestAssetPartitionMaterializationAttemptsWithoutMaterializations"
        ]

        # Translate list to tuple
        return {key: tuple(val) for key, val in result.items()}

    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Mapping[str, str] | None = None,
        filter_event_id: int | None = None,
    ) -> Sequence[Mapping[str, str]]:
        check.inst_param(asset_key, "asset_key", AssetKey)
        filter_tags = check.opt_mapping_param(
            filter_tags, "filter_tags", key_type=str, value_type=str
        )

        res = self._execute_query(
            GET_EVENT_TAGS_FOR_ASSET,
            variables={
                "assetKey": asset_key.to_string(),
                "filterTags": [{"key": key, "value": value} for key, value in filter_tags.items()],
                "filterEventId": filter_event_id,
            },
        )
        tags_result = res["data"]["eventLogs"]["getAssetEventTags"]
        return [
            {event_tag["key"]: event_tag["value"] for event_tag in event_tags["tags"]}
            for event_tags in tags_result
        ]

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        check.str_param(partitions_def_name, "partitions_def_name")
        res = self._execute_query(
            GET_DYNAMIC_PARTITIONS_QUERY,
            variables={"partitionsDefName": partitions_def_name},
        )
        return res["data"]["eventLogs"]["getDynamicPartitions"]

    def get_paginated_dynamic_partitions(
        self, partitions_def_name: str, limit: int, ascending: bool, cursor: str | None = None
    ) -> PaginatedResults[str]:
        check.str_param(partitions_def_name, "partitions_def_name")
        check.int_param(limit, "limit")
        check.bool_param(ascending, "ascending")
        check.opt_str_param(cursor, "cursor")
        res = self._execute_query(
            GET_PAGINATED_DYNAMIC_PARTITIONS_QUERY,
            variables={
                "partitionsDefName": partitions_def_name,
                "limit": limit,
                "ascending": ascending,
                "cursor": cursor,
            },
        )
        return PaginatedResults(
            results=res["data"]["eventLogs"]["getPaginatedDynamicPartitions"]["results"],
            cursor=res["data"]["eventLogs"]["getPaginatedDynamicPartitions"]["cursor"],
            has_more=res["data"]["eventLogs"]["getPaginatedDynamicPartitions"]["hasMore"],
        )

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_key")
        res = self._execute_query(
            HAS_DYNAMIC_PARTITION_QUERY,
            variables={
                "partitionsDefName": partitions_def_name,
                "partitionKey": partition_key,
            },
        )
        return res["data"]["eventLogs"]["hasDynamicPartition"]

    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        check.str_param(partitions_def_name, "partitions_def_name")
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        self._execute_query(
            ADD_DYNAMIC_PARTITIONS_MUTATION,
            variables={
                "partitionsDefName": partitions_def_name,
                "partitionKeys": partition_keys,
            },
        )

    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_key")
        self._execute_query(
            DELETE_DYNAMIC_PARTITION_MUTATION,
            variables={
                "partitionsDefName": partitions_def_name,
                "partitionKey": partition_key,
            },
        )

    def wipe_asset(self, asset_key: AssetKey):
        res = self._execute_query(
            WIPE_ASSET_MUTATION, variables={"assetKey": asset_key.to_string()}
        )
        return res

    def wipe_asset_partitions(self, asset_key: AssetKey, partition_keys: Sequence[str]):
        """Remove asset index history from event log for given asset partitions."""
        res = self._execute_query(
            WIPE_ASSET_PARTITIONS_MUTATION,
            variables={
                "assetKey": asset_key.to_string(),
                "partitionKeys": partition_keys,
            },
        )
        return res

    @property
    def supports_global_concurrency_limits(self) -> bool:
        return True

    def initialize_concurrency_limit_to_default(self, concurrency_key: str) -> bool:
        check.str_param(concurrency_key, "concurrency_key")
        res = self._execute_query(
            INITIALIZE_CONCURRENCY_LIMIT_MUTATION,
            variables={"concurrencyKey": concurrency_key},
            idempotent_mutation=True,
        )
        result = res["data"]["eventLogs"]["InitializeConcurrencyLimit"]
        error = result.get("error")

        if error:
            if error["className"] == "DagsterInvalidInvocationError":
                raise DagsterInvalidInvocationError(error["message"])
            else:
                raise DagsterCloudAgentServerError(res)
        return result.get("success")

    def set_concurrency_slots(self, concurrency_key: str, num: int) -> None:
        check.str_param(concurrency_key, "concurrency_key")
        check.int_param(num, "num")
        res = self._execute_query(
            SET_CONCURRENCY_SLOTS_MUTATION,
            variables={"concurrencyKey": concurrency_key, "num": num},
        )
        result = res["data"]["eventLogs"]["SetConcurrencySlots"]
        error = result.get("error")

        if error:
            if error["className"] == "DagsterInvalidInvocationError":
                raise DagsterInvalidInvocationError(error["message"])
            else:
                raise DagsterCloudAgentServerError(res)
        return res

    def delete_concurrency_limit(self, concurrency_key: str) -> None:
        check.str_param(concurrency_key, "concurrency_key")
        res = self._execute_query(
            DELETE_CONCURRENCY_LIMIT_MUTATION,
            variables={"concurrencyKey": concurrency_key},
        )
        result = res["data"]["eventLogs"]["DeleteConcurrencyLimit"]
        error = result.get("error")
        if error:
            if error["className"] == "DagsterInvalidInvocationError":
                raise DagsterInvalidInvocationError(error["message"])
            else:
                raise DagsterCloudAgentServerError(res)

    def get_concurrency_keys(self) -> set[str]:
        res = self._execute_query(GET_CONCURRENCY_KEYS_QUERY)
        return set(res["data"]["eventLogs"]["getConcurrencyKeys"])

    def get_concurrency_info(self, concurrency_key: str) -> ConcurrencyKeyInfo:
        check.str_param(concurrency_key, "concurrency_key")
        res = self._execute_query(
            GET_CONCURRENCY_INFO_QUERY,
            variables={"concurrencyKey": concurrency_key},
        )
        info = res["data"]["eventLogs"]["getConcurrencyInfo"]
        return ConcurrencyKeyInfo(
            concurrency_key=concurrency_key,
            slot_count=info["slotCount"],
            claimed_slots=[_claimed_slot_from_graphql(slot) for slot in info["claimedSlots"]],
            pending_steps=[_pending_step_from_graphql(step) for step in info["pendingSteps"]],
            limit=info["limit"],
            using_default_limit=bool(info["usingDefaultLimit"]),
        )

    def claim_concurrency_slot(
        self, concurrency_key: str, run_id: str, step_key: str, priority: int | None = None
    ) -> ConcurrencyClaimStatus:
        check.str_param(concurrency_key, "concurrency_key")
        check.str_param(run_id, "run_id")
        check.str_param(step_key, "step_key")
        check.opt_int_param(priority, "priority")
        res = self._execute_query(
            CLAIM_CONCURRENCY_SLOT_MUTATION,
            variables={
                "concurrencyKey": concurrency_key,
                "runId": run_id,
                "stepKey": step_key,
                "priority": priority or 0,
            },
            idempotent_mutation=True,
        )
        claim_status = res["data"]["eventLogs"]["ClaimConcurrencySlot"]["status"]
        return ConcurrencyClaimStatus(
            concurrency_key=concurrency_key,
            slot_status=ConcurrencySlotStatus(claim_status["slotStatus"]),
            priority=claim_status["priority"],
            assigned_timestamp=(
                datetime_from_timestamp(claim_status["assignedTimestamp"])
                if claim_status["assignedTimestamp"]
                else None
            ),
            enqueued_timestamp=(
                datetime_from_timestamp(claim_status["enqueuedTimestamp"])
                if claim_status["enqueuedTimestamp"]
                else None
            ),
        )

    def check_concurrency_claim(
        self, concurrency_key: str, run_id: str, step_key: str
    ) -> ConcurrencyClaimStatus:
        check.str_param(concurrency_key, "concurrency_key")
        check.str_param(run_id, "run_id")
        check.str_param(step_key, "step_key")
        res = self._execute_query(
            CHECK_CONCURRENCY_CLAIM_QUERY,
            variables={
                "concurrencyKey": concurrency_key,
                "runId": run_id,
                "stepKey": step_key,
            },
        )
        claim_status = res["data"]["eventLogs"]["getCheckConcurrencyClaim"]
        return ConcurrencyClaimStatus(
            concurrency_key=concurrency_key,
            slot_status=ConcurrencySlotStatus(claim_status["slotStatus"]),
            priority=claim_status["priority"],
            assigned_timestamp=(
                datetime_from_timestamp(claim_status["assignedTimestamp"])
                if claim_status["assignedTimestamp"]
                else None
            ),
            enqueued_timestamp=(
                datetime_from_timestamp(claim_status["enqueuedTimestamp"])
                if claim_status["enqueuedTimestamp"]
                else None
            ),
        )

    def get_concurrency_run_ids(self) -> set[str]:
        raise NotImplementedError("Not callable from user cloud")

    def free_concurrency_slots_for_run(self, run_id: str) -> None:
        check.str_param(run_id, "run_id")
        res = self._execute_query(
            FREE_CONCURRENCY_SLOTS_FOR_RUN_MUTATION,
            variables={"runId": run_id},
            idempotent_mutation=True,
        )
        return res

    def free_concurrency_slot_for_step(self, run_id: str, step_key: str) -> None:
        check.str_param(run_id, "run_id")
        check.opt_str_param(step_key, "step_key")
        res = self._execute_query(
            FREE_CONCURRENCY_SLOT_FOR_STEP_MUTATION,
            variables={"runId": run_id, "stepKey": step_key},
            idempotent_mutation=True,
        )
        return res

    def get_asset_check_execution_history(
        self,
        check_key: AssetCheckKey,
        limit: int,
        cursor: int | None = None,
        status: AbstractSet[AssetCheckExecutionRecordStatus] | None = None,
        partition_filter: PartitionKeyFilter | None = None,
    ) -> Sequence[AssetCheckExecutionRecord]:
        raise NotImplementedError("Not callable from user cloud")

    def get_latest_asset_check_execution_by_key(
        self,
        check_keys: Sequence[AssetCheckKey],
        partition_filter: PartitionKeyFilter | None = None,
    ) -> Mapping[AssetCheckKey, AssetCheckExecutionRecord]:
        if not check_keys:
            return {}
        res = self._execute_query(
            GET_LATEST_ASSET_CHECK_EXECUTION_BY_KEY_QUERY,
            variables={
                "assetCheckKeys": [key.to_user_string() for key in check_keys],
                "partitionFilter": (
                    {"key": partition_filter.key} if partition_filter is not None else None
                ),
            },
        )
        records = {}
        for result in res["data"]["eventLogs"]["getLatestAssetCheckExecutionByKey"]:
            check_key = AssetCheckKey.from_graphql_input(result["assetCheckKey"])
            records[check_key] = _asset_check_execution_record_from_graphql(result, check_key)
        return records

    def get_asset_check_partition_info(
        self,
        keys: Sequence[AssetCheckKey],
        after_storage_id: int | None = None,
        partition_keys: Sequence[str] | None = None,
    ) -> Sequence[AssetCheckPartitionInfo]:
        raise NotImplementedError("Not callable from user cloud")

    def fetch_materializations(
        self,
        records_filter: AssetKey | AssetRecordsFilter,
        limit: int,
        cursor: str | None = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        res = self._execute_query(
            FETCH_MATERIALIZATIONS_QUERY,
            variables={
                "recordsFilter": _get_asset_records_filter_input(records_filter),
                "limit": limit,
                "cursor": cursor,
                "ascending": ascending,
            },
        )
        return _event_records_result_from_graphql(res["data"]["eventLogs"]["fetchMaterializations"])

    def fetch_failed_materializations(
        self,
        records_filter: AssetKey | AssetRecordsFilter,
        limit: int,
        cursor: str | None = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        res = self._execute_query(
            FETCH_FAILED_MATERIALIZATIONS_QUERY,
            variables={
                "recordsFilter": _get_asset_records_filter_input(records_filter),
                "limit": limit,
                "cursor": cursor,
                "ascending": ascending,
            },
        )
        return _event_records_result_from_graphql(
            res["data"]["eventLogs"]["fetchFailedMaterializations"]
        )

    def fetch_observations(
        self,
        records_filter: AssetKey | AssetRecordsFilter,
        limit: int,
        cursor: str | None = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        res = self._execute_query(
            FETCH_OBSERVATIONS_QUERY,
            variables={
                "recordsFilter": _get_asset_records_filter_input(records_filter),
                "limit": limit,
                "cursor": cursor,
                "ascending": ascending,
            },
        )
        return _event_records_result_from_graphql(res["data"]["eventLogs"]["fetchObservations"])

    def fetch_planned_materializations(
        self,
        records_filter: AssetKey | AssetRecordsFilter,
        limit: int,
        cursor: str | None = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        res = self._execute_query(
            FETCH_PLANNED_MATERIALIZATIONS,
            variables={
                "recordsFilter": _get_asset_records_filter_input(records_filter),
                "limit": limit,
                "cursor": cursor,
                "ascending": ascending,
            },
        )
        return _event_records_result_from_graphql(
            res["data"]["eventLogs"]["fetchPlannedMaterializations"]
        )

    @property
    def supports_run_status_change_job_name_filter(self):
        return True

    def fetch_run_status_changes(
        self,
        records_filter: DagsterEventType | RunStatusChangeRecordsFilter,
        limit: int,
        cursor: str | None = None,
        ascending: bool = False,
    ) -> EventRecordsResult:
        res = self._execute_query(
            GET_RUN_STATUS_CHANGE_EVENTS_QUERY,
            variables={
                "recordsFilter": _fetch_run_status_changes_filter_input(records_filter),
                "limit": limit,
                "cursor": cursor,
                "ascending": ascending,
            },
        )
        return _event_records_result_from_graphql(
            res["data"]["eventLogs"]["getRunStatusChangeEventRecords"]
        )

    def get_latest_planned_materialization_info(
        self,
        asset_key: AssetKey,
        partition: str | None = None,
    ) -> PlannedMaterializationInfo | None:
        res = self._execute_query(
            GET_LATEST_PLANNED_MATERIALIZATION_INFO,
            variables={
                "assetKey": asset_key.to_string(),
                "partition": partition,
            },
        )
        info = res["data"]["eventLogs"]["getLatestPlannedMaterializationInfo"]
        if info["runId"] and info["storageId"]:
            return PlannedMaterializationInfo(
                storage_id=int(info["storageId"]),
                run_id=info["runId"],
            )
        return None

    def get_updated_data_version_partitions(
        self, asset_key: AssetKey, partitions: Iterable[str], since_storage_id: int
    ) -> set[str]:
        res = self._execute_query(
            GET_UPDATED_DATA_VERSION_PARTITIONS,
            variables={
                "assetKey": asset_key.to_string(),
                "partitions": list(partitions),
                "afterStorageId": since_storage_id,
            },
        )
        partitions = res["data"]["eventLogs"]["getUpdatedDataVersionPartitions"]
        return set(partitions)

    @property
    def handles_run_events_in_store_event(self) -> bool:
        return True

    def default_run_scoped_event_tailer_offset(self) -> int:
        return DEFAULT_RUN_SCOPED_EVENT_TAILER_OFFSET

    def get_asset_status_cache_values(
        self,
        partitions_defs_by_key: Iterable[tuple[AssetKey, PartitionsDefinition | None]],
        context,
    ) -> Sequence[AssetStatusCacheValue | None]:
        asset_keys = [key for key, _ in partitions_defs_by_key]
        res = self._execute_query(
            GET_ASSET_STATUS_CACHE_VALUES,
            variables={
                "assetKeys": [asset_key.to_graphql_input() for asset_key in asset_keys],
            },
        )

        return [
            AssetStatusCacheValue(
                latest_storage_id=value["latestStorageId"],
                partitions_def_id=value["partitionsDefId"],
                serialized_materialized_partition_subset=value[
                    "serializedMaterializedPartitionSubset"
                ],
                serialized_failed_partition_subset=value["serializedFailedPartitionSubset"],
                serialized_in_progress_partition_subset=value[
                    "serializedInProgressPartitionSubset"
                ],
                earliest_in_progress_materialization_event_id=value[
                    "earliestInProgressMaterializationEventId"
                ],
            )
            if value
            else None
            for value in res["data"]["eventLogs"]["getAssetStatusCacheValues"]
        ]

    def get_pool_config(self):
        res = self._execute_query(GET_POOL_CONFIG_QUERY)
        pool_config = res["data"]["eventLogs"]["getPoolConfig"]
        granularity_str = pool_config.get("poolGranularity")

        return PoolConfig(
            pool_granularity=PoolGranularity(granularity_str) if granularity_str else None,
            default_pool_limit=pool_config.get("defaultPoolLimit"),
            op_granularity_run_buffer=pool_config.get("opGranularityRunBuffer"),
        )

    def get_pool_limits(self) -> Sequence[PoolLimit]:
        """Get the set of concurrency limited keys and limits."""
        res = self._execute_query(GET_POOL_LIMITS_QUERY)
        limits = res["data"]["eventLogs"]["getPoolLimits"]
        return [
            PoolLimit(
                name=limit.get("name"),
                limit=limit.get("limit"),
                from_default=limit.get("fromDefault"),
            )
            for limit in limits
        ]
