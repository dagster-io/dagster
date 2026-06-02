import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

import dagster._check as check
from dagster._core.errors import (
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunNotFoundError,
    DagsterSnapshotDoesNotExist,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus, PartitionBackfill
from dagster._core.execution.telemetry import RunTelemetryData
from dagster._core.remote_origin import RemoteJobOrigin
from dagster._core.snap import ExecutionPlanSnapshot, JobSnap, create_execution_plan_snapshot_id
from dagster._core.storage.dagster_run import (
    DagsterRun,
    JobBucket,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._core.storage.runs.base import RunStorage
from dagster._daemon.types import DaemonHeartbeat
from dagster._serdes import (
    ConfigurableClass,
    ConfigurableClassData,
    deserialize_value,
    serialize_value,
)
from dagster._time import datetime_from_timestamp
from dagster._utils.merger import merge_dicts
from dagster_cloud_cli.core.errors import DagsterCloudAgentServerError
from typing_extensions import Self

from dagster_cloud.storage.runs.queries import (
    ADD_BACKFILL_MUTATION,
    ADD_DAEMON_HEARTBEAT_MUTATION,
    ADD_EXECUTION_PLAN_SNAPSHOT_MUTATION,
    ADD_HISTORICAL_RUN_MUTATION,
    ADD_PIPELINE_SNAPSHOT_MUTATION,
    ADD_RUN_MUTATION,
    ADD_RUN_TAGS_MUTATION,
    ADD_RUN_TELEMETRY_MUTATION,
    GET_BACKFILL_QUERY,
    GET_BACKFILLS_QUERY,
    GET_DAEMON_HEARTBEATS_QUERY,
    GET_EXECUTION_PLAN_SNAPSHOT_QUERY,
    GET_PIPELINE_SNAPSHOT_QUERY,
    GET_RUN_BY_ID_QUERY,
    GET_RUN_GROUP_QUERY,
    GET_RUN_IDS_QUERY,
    GET_RUN_PARTITION_DATA_QUERY,
    GET_RUN_RECORDS_QUERY,
    GET_RUN_TAG_KEYS_QUERY,
    GET_RUN_TAGS_QUERY,
    GET_RUNS_COUNT_QUERY,
    GET_RUNS_QUERY,
    HAS_EXECUTION_PLAN_SNAPSHOT_QUERY,
    HAS_PIPELINE_SNAPSHOT_QUERY,
    HAS_RUN_QUERY,
    MUTATE_JOB_ORIGIN,
    UPDATE_BACKFILL_MUTATION,
)


def _get_filters_input(filters: RunsFilter | None) -> dict[str, Any] | None:
    filters = check.opt_inst_param(filters, "filters", RunsFilter)

    if filters is None:
        return None

    check.invariant(filters.exclude_subruns is None, "RunsFilter.exclude_subruns is not supported")
    return {
        "runIds": filters.run_ids,
        "pipelineName": filters.job_name,
        "statuses": [status.value for status in filters.statuses],
        "tags": (
            [
                merge_dicts(
                    {"key": tag_key},
                    ({"value": tag_value} if isinstance(tag_value, str) else {"values": tag_value}),
                )
                for tag_key, tag_value in filters.tags.items()
            ]
            if filters.tags
            else []
        ),
        "snapshotId": filters.snapshot_id,
        "updatedAfter": filters.updated_after.timestamp() if filters.updated_after else None,
        "updatedBefore": filters.updated_before.timestamp() if filters.updated_before else None,
        "createdAfter": filters.created_after.timestamp() if filters.created_after else None,
        "createdBefore": filters.created_before.timestamp() if filters.created_before else None,
    }


def _get_bulk_actions_filters_input(
    filters: BulkActionsFilter | None,
) -> dict[str, Any] | None:
    filters = check.opt_inst_param(filters, "filters", BulkActionsFilter)
    unsupported_filters = []
    if filters and filters.job_name:
        unsupported_filters.append("job_name")
    if filters and filters.backfill_ids:
        unsupported_filters.append("backfill_ids")
    if filters and filters.tags:
        unsupported_filters.append("tags")

    check.invariant(
        len(unsupported_filters) == 0,
        f"Used the following unsupported filters: {', '.join(unsupported_filters)}.",
    )

    if filters is None:
        return None
    return {
        "statuses": [status.value for status in filters.statuses] if filters.statuses else None,
        "createdAfter": filters.created_after.timestamp() if filters.created_after else None,
        "createdBefore": filters.created_before.timestamp() if filters.created_before else None,
    }


def _run_record_from_graphql(graphene_run_record: dict) -> RunRecord:
    check.dict_param(graphene_run_record, "graphene_run_record")
    return RunRecord(
        storage_id=check.int_elem(graphene_run_record, "storageId"),
        dagster_run=deserialize_value(
            check.str_elem(graphene_run_record, "serializedPipelineRun"),
            DagsterRun,
        ),
        create_timestamp=datetime_from_timestamp(
            check.float_elem(graphene_run_record, "createTimestamp")
        ),
        update_timestamp=datetime_from_timestamp(
            check.float_elem(graphene_run_record, "updateTimestamp")
        ),
        start_time=graphene_run_record.get("startTime"),
        end_time=graphene_run_record.get("endTime"),
    )


def _get_bucket_input(bucket_by: JobBucket | TagBucket | None) -> dict[str, Any] | None:
    if not bucket_by:
        return None

    bucket_type = "job" if isinstance(bucket_by, JobBucket) else "tag"
    tag_key = bucket_by.tag_key if isinstance(bucket_by, TagBucket) else None
    values = bucket_by.job_names if isinstance(bucket_by, JobBucket) else bucket_by.tag_values
    return {
        "bucketType": bucket_type,
        "tagKey": tag_key,
        "values": values,
        "bucketLimit": bucket_by.bucket_limit,
    }


class GraphQLRunStorage(RunStorage, ConfigurableClass):
    def __init__(
        self, inst_data: ConfigurableClassData | None = None, override_graphql_client=None
    ):
        """Initialize this class directly only for test (using `override_graphql_client`).
        Use the ConfigurableClass machinery to init from instance yaml.
        """
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._override_graphql_client = override_graphql_client

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

    def _execute_query(self, query, variables=None, idempotent_mutation=False):
        return self._graphql_client.execute(
            query, variable_values=variables, idempotent_mutation=idempotent_mutation
        )

    def add_historical_run(
        self, dagster_run: DagsterRun, run_creation_time: datetime
    ) -> DagsterRun:
        check.inst_param(dagster_run, "dagster_run", DagsterRun)
        res = self._execute_query(
            ADD_HISTORICAL_RUN_MUTATION,
            variables={
                "serializedPipelineRun": serialize_value(dagster_run),
                "runCreationTime": run_creation_time.timestamp(),
            },
        )
        result = res["data"]["runs"]["addHistoricalRun"]
        error = result.get("error")
        # Special-case some errors to match the RunStorage API
        if error:
            if error["className"] == "DagsterRunAlreadyExists":
                raise DagsterRunAlreadyExists(error["message"])
            if error["className"] == "DagsterSnapshotDoesNotExist":
                raise DagsterSnapshotDoesNotExist(error["message"])
            else:
                raise DagsterCloudAgentServerError(res)
        return dagster_run

    def add_run(self, dagster_run: DagsterRun):
        check.inst_param(dagster_run, "dagster_run", DagsterRun)
        res = self._execute_query(
            ADD_RUN_MUTATION,
            variables={"serializedPipelineRun": serialize_value(dagster_run)},
        )

        result = res["data"]["runs"]["addRun"]
        error = result.get("error")

        # Special-case some errors to match the RunStorage API
        if error:
            if error["className"] == "DagsterRunAlreadyExists":
                raise DagsterRunAlreadyExists(error["message"])
            if error["className"] == "DagsterSnapshotDoesNotExist":
                raise DagsterSnapshotDoesNotExist(error["message"])
            else:
                raise DagsterCloudAgentServerError(res)

        return dagster_run

    def handle_run_event(
        self, run_id: str, event: DagsterEvent, update_timestamp: datetime | None = None
    ):
        raise NotImplementedError("Should never be called by an agent client")

    @property
    def supports_bucket_queries(self) -> bool:
        return False

    def get_runs(  # ty: ignore[invalid-method-override], fix me!
        self,
        filters: RunsFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        bucket_by: JobBucket | TagBucket | None = None,
        ascending: bool = False,
    ) -> Iterable[DagsterRun]:
        res = self._execute_query(
            GET_RUNS_QUERY,
            variables={
                "filters": _get_filters_input(filters),
                "cursor": check.opt_str_param(cursor, "cursor"),
                "limit": check.opt_int_param(limit, "limit"),
                "bucketBy": _get_bucket_input(bucket_by),
                "ascending": check.bool_param(ascending, "ascending"),
            },
        )
        return [deserialize_value(run, DagsterRun) for run in res["data"]["runs"]["getRuns"]]

    def get_run_ids(
        self,
        filters: RunsFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Sequence[str]:
        res = self._execute_query(
            GET_RUN_IDS_QUERY,
            variables={
                "filters": _get_filters_input(filters),
                "cursor": check.opt_str_param(cursor, "cursor"),
                "limit": check.opt_int_param(limit, "limit"),
            },
        )
        return res["data"]["runs"]["getRunIds"]

    def get_runs_count(self, filters: RunsFilter | None = None) -> int:
        res = self._execute_query(
            GET_RUNS_COUNT_QUERY,
            variables={
                "filters": _get_filters_input(filters),
            },
        )
        return res["data"]["runs"]["getRunsCount"]

    def get_run_group(self, run_id: str) -> tuple[str, Iterable[DagsterRun]] | None:  # ty: ignore[invalid-method-override], fix me!
        res = self._execute_query(
            GET_RUN_GROUP_QUERY, variables={"runId": check.str_param(run_id, "run_id")}
        )
        run_group_or_error = res["data"]["runs"]["getRunGroupOrError"]
        if run_group_or_error["__typename"] == "SerializedRunGroup":
            return (
                run_group_or_error["rootRunId"],
                [
                    deserialize_value(run, DagsterRun)
                    for run in run_group_or_error["serializedRuns"]
                ],
            )
        elif run_group_or_error["__typename"] == "RunNotFoundError":
            raise DagsterRunNotFoundError(invalid_run_id=run_group_or_error["runId"])
        else:
            raise DagsterInvariantViolationError(f"Unexpected getRunGroupOrError response {res}")

    def get_run_by_id(self, run_id: str) -> DagsterRun | None:
        res = self._execute_query(
            GET_RUN_BY_ID_QUERY, variables={"runId": check.str_param(run_id, "run_id")}
        )
        run = res["data"]["runs"]["getRunById"]
        if run is None:
            return None

        return deserialize_value(run, DagsterRun)

    def get_run_records(
        self,
        filters: RunsFilter | None = None,
        limit: int | None = None,
        order_by: str | None = None,
        ascending: bool = False,
        cursor: str | None = None,
        bucket_by: JobBucket | TagBucket | None = None,
    ) -> list[RunRecord]:
        res = self._execute_query(
            GET_RUN_RECORDS_QUERY,
            variables={
                "filters": _get_filters_input(filters),
                "limit": check.opt_int_param(limit, "limit"),
                "orderBy": check.opt_str_param(order_by, "order_by"),
                "ascending": check.opt_bool_param(ascending, "ascending"),
                "cursor": check.opt_str_param(cursor, "cursor"),
                "bucketBy": _get_bucket_input(bucket_by),
            },
        )
        return [_run_record_from_graphql(record) for record in res["data"]["runs"]["getRunRecords"]]

    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: str | None = None,
        limit: int | None = None,
    ) -> Sequence[tuple[str, set[str]]]:
        res = self._execute_query(
            GET_RUN_TAGS_QUERY,
            variables={
                "jsonTagKeys": (json.dumps(check.list_param(tag_keys, "tag_keys", of_type=str))),
                "valuePrefix": check.opt_str_param(value_prefix, "value_prefix"),
                "limit": check.opt_int_param(limit, "limit"),
            },
        )
        return [
            (run_tag["key"], set(run_tag["values"]))
            for run_tag in res["data"]["runs"]["getRunTags"]
        ]

    def get_run_tag_keys(self) -> Sequence[str]:
        res = self._execute_query(GET_RUN_TAG_KEYS_QUERY)
        return [run_tag_key for run_tag_key in res["data"]["runs"]["getRunTagKeys"]]

    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]):
        self._execute_query(
            ADD_RUN_TAGS_MUTATION,
            variables={
                "runId": check.str_param(run_id, "run_id"),
                "jsonNewTags": json.dumps(
                    check.mapping_param(new_tags, "new_tags", key_type=str, value_type=str)
                ),
            },
            idempotent_mutation=True,
        )

    def has_run(self, run_id: str) -> bool:
        res = self._execute_query(
            HAS_RUN_QUERY, variables={"runId": check.str_param(run_id, "run_id")}
        )
        return res["data"]["runs"]["hasRun"]

    def has_job_snapshot(self, pipeline_snapshot_id: str) -> bool:  # ty: ignore[invalid-method-override], fix me!
        res = self._execute_query(
            HAS_PIPELINE_SNAPSHOT_QUERY,
            variables={
                "pipelineSnapshotId": check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
            },
        )
        return res["data"]["runs"]["hasPipelineSnapshot"]

    def add_job_snapshot(  # ty: ignore[invalid-method-override], fix me!
        self, pipeline_snapshot: JobSnap, snapshot_id: str | None = None
    ) -> str:
        self._execute_query(
            ADD_PIPELINE_SNAPSHOT_MUTATION,
            variables={
                "serializedPipelineSnapshot": serialize_value(
                    check.inst_param(pipeline_snapshot, "pipeline_snapshot", JobSnap)
                ),
                "snapshotId": snapshot_id,
            },
        )
        return snapshot_id if snapshot_id else pipeline_snapshot.snapshot_id

    def get_job_snapshot(self, pipeline_snapshot_id: str) -> JobSnap:  # ty: ignore[invalid-method-override], fix me!
        res = self._execute_query(
            GET_PIPELINE_SNAPSHOT_QUERY,
            variables={
                "pipelineSnapshotId": check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
            },
        )
        return deserialize_value(res["data"]["runs"]["getPipelineSnapshot"], JobSnap)

    def has_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> bool:
        res = self._execute_query(
            HAS_EXECUTION_PLAN_SNAPSHOT_QUERY,
            variables={
                "executionPlanSnapshotId": check.str_param(
                    execution_plan_snapshot_id, "execution_plan_snapshot_id"
                )
            },
        )
        return res["data"]["runs"]["hasExecutionPlanSnapshot"]

    def add_execution_plan_snapshot(
        self, execution_plan_snapshot: ExecutionPlanSnapshot, snapshot_id: str | None = None
    ) -> str:
        res = self._execute_query(
            ADD_EXECUTION_PLAN_SNAPSHOT_MUTATION,
            variables={
                "serializedExecutionPlanSnapshot": serialize_value(
                    check.inst_param(
                        execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
                    )
                ),
                "snapshotId": snapshot_id,
            },
        )
        server_snapshot_id = res["data"]["runs"]["addExecutionPlanSnapshot"].get("snapshotId")
        if server_snapshot_id is not None:
            return server_snapshot_id
        return (
            snapshot_id
            if snapshot_id
            else create_execution_plan_snapshot_id(execution_plan_snapshot)
        )

    def get_execution_plan_snapshot(self, execution_plan_snapshot_id: str) -> ExecutionPlanSnapshot:
        res = self._execute_query(
            GET_EXECUTION_PLAN_SNAPSHOT_QUERY,
            variables={
                "executionPlanSnapshotId": check.str_param(
                    execution_plan_snapshot_id, "execution_plan_snapshot_id"
                )
            },
        )
        return deserialize_value(
            res["data"]["runs"]["getExecutionPlanSnapshot"], ExecutionPlanSnapshot
        )

    def get_run_partition_data(self, runs_filter: RunsFilter) -> list[RunPartitionData]:
        res = self._execute_query(
            GET_RUN_PARTITION_DATA_QUERY,
            variables={
                "runsFilter": _get_filters_input(runs_filter),
            },
        )
        return [
            deserialize_value(result, RunPartitionData)
            for result in res["data"]["runs"]["getRunPartitionData"]
        ]

    def add_daemon_heartbeat(self, daemon_heartbeat: DaemonHeartbeat):
        self._execute_query(
            ADD_DAEMON_HEARTBEAT_MUTATION,
            variables={
                "serializedDaemonHeartbeat": serialize_value(
                    check.inst_param(daemon_heartbeat, "daemon_heartbeat", DaemonHeartbeat)
                )
            },
        )

    def supports_run_telemetry(self) -> bool:
        return True

    def add_run_telemetry(
        self,
        run_telemetry: RunTelemetryData,
        tags: dict[str, str] | None = None,
    ) -> None:
        if tags is None:
            tags = {}

        self._execute_query(
            ADD_RUN_TELEMETRY_MUTATION,
            variables={
                "serializedTelemetry": serialize_value(
                    check.inst_param(run_telemetry, "run_telemetry", RunTelemetryData)
                ),
                "serializedTags": serialize_value(
                    check.dict_param(tags, "tags", key_type=str, value_type=str)
                ),
            },
        )

    def build_missing_indexes(
        self, print_fn: Callable = lambda _: None, force_rebuild_all: bool = False
    ):
        raise Exception("Not allowed to build indexes from user cloud")

    def get_daemon_heartbeats(self) -> dict[str, DaemonHeartbeat]:
        res = self._execute_query(GET_DAEMON_HEARTBEATS_QUERY)
        return {
            key: deserialize_value(heartbeat, DaemonHeartbeat)
            for key, heartbeat in json.loads(res["data"]["runs"]["getDaemonHeartbeats"]).items()
        }

    def delete_run(self, run_id: str):
        raise Exception("Not allowed to delete runs from user cloud")

    def wipe_daemon_heartbeats(self):
        raise Exception("Not allowed to wipe heartbeats from user cloud")

    def wipe(self):
        raise Exception("Not allowed to wipe runs from user cloud")

    def has_bulk_actions_table(self) -> bool:
        return False

    def get_backfills(
        self,
        filters: BulkActionsFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
        status: BulkActionStatus | None = None,
    ):
        """Get a list of partition backfills."""
        res = self._execute_query(
            GET_BACKFILLS_QUERY,
            variables={
                "status": status.value if status else None,
                "cursor": check.opt_str_param(cursor, "cursor"),
                "limit": check.opt_int_param(limit, "limit"),
                "filters": _get_bulk_actions_filters_input(filters),
            },
        )
        return [
            deserialize_value(backfill, PartitionBackfill)
            for backfill in res["data"]["runs"]["getBackfills"]
        ]

    def get_backfills_count(self, filters: BulkActionsFilter | None = None) -> int:
        raise NotImplementedError("get_backfills_count is not callable from user cloud.")

    def get_backfill(self, backfill_id: str) -> PartitionBackfill:
        """Get a single partition backfill."""
        res = self._execute_query(GET_BACKFILL_QUERY, variables={"backfillId": backfill_id})
        backfill = res["data"]["runs"]["getBackfill"]
        return deserialize_value(backfill, PartitionBackfill)

    def add_backfill(self, partition_backfill: PartitionBackfill):
        """Add partition backfill to run storage."""
        self._execute_query(
            ADD_BACKFILL_MUTATION,
            variables={"serializedPartitionBackfill": serialize_value(partition_backfill)},
        )

    def update_backfill(self, partition_backfill: PartitionBackfill):
        """Update a partition backfill in run storage."""
        self._execute_query(
            UPDATE_BACKFILL_MUTATION,
            variables={"serializedPartitionBackfill": serialize_value(partition_backfill)},
        )

    def get_cursor_values(self, keys: set[str]):
        return NotImplementedError("KVS is not supported from the user cloud")

    def set_cursor_values(self, pairs: Mapping[str, str]):
        return NotImplementedError("KVS is not supported from the user cloud")

    # Migrating run history
    def replace_job_origin(self, run: DagsterRun, job_origin: RemoteJobOrigin):
        self._execute_query(
            MUTATE_JOB_ORIGIN,
            variables={
                "runId": run.run_id,
                "serializedJobOrigin": serialize_value(job_origin),
            },
        )
