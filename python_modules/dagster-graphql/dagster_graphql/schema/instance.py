import sys
from typing import TYPE_CHECKING

import dagster._check as check
import graphene
import yaml
from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import PoolConfig
from dagster._core.launcher.base import RunLauncher
from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage
from dagster._daemon.asset_daemon import get_auto_materialize_paused
from dagster._daemon.types import DaemonStatus
from dagster._utils.concurrency import (
    ClaimedSlotInfo,
    PendingStepInfo,
    get_max_concurrency_limit_value,
)

from dagster_graphql.schema.errors import GraphenePythonError
from dagster_graphql.schema.util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster._core.run_coordinator.queued_run_coordinator import RunQueueConfig


class GrapheneRunLauncher(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)

    class Meta:
        name = "RunLauncher"

    def __init__(self, run_launcher):
        super().__init__()
        self._run_launcher = check.inst_param(run_launcher, "run_launcher", RunLauncher)

    def resolve_name(self, _graphene_info: ResolveInfo):
        return self._run_launcher.__class__.__name__


class GrapheneDaemonStatus(graphene.ObjectType):
    daemonType = graphene.NonNull(graphene.String)
    id = graphene.NonNull(graphene.ID)
    required = graphene.NonNull(graphene.Boolean)
    healthy = graphene.Boolean()
    lastHeartbeatTime = graphene.Float()
    lastHeartbeatErrors = non_null_list(GraphenePythonError)

    class Meta:
        name = "DaemonStatus"

    def __init__(self, daemon_status):
        check.inst_param(daemon_status, "daemon_status", DaemonStatus)

        super().__init__(
            daemonType=daemon_status.daemon_type,
            required=daemon_status.required,
            healthy=daemon_status.healthy,
            lastHeartbeatTime=(
                daemon_status.last_heartbeat.timestamp if daemon_status.last_heartbeat else None
            ),
            lastHeartbeatErrors=(
                [GraphenePythonError(error) for error in daemon_status.last_heartbeat.errors]
                if daemon_status.last_heartbeat and daemon_status.last_heartbeat.errors
                else []
            ),
        )

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self.daemonType


class GrapheneDaemonHealth(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    daemonStatus = graphene.Field(
        graphene.NonNull(GrapheneDaemonStatus),
        daemon_type=graphene.Argument(graphene.String),
    )
    allDaemonStatuses = non_null_list(GrapheneDaemonStatus)

    class Meta:
        name = "DaemonHealth"

    def __init__(self, instance):
        super().__init__()
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_id(self, _graphene_info: ResolveInfo):
        return "daemonHealth"

    def resolve_daemonStatus(self, _graphene_info: ResolveInfo, daemon_type):
        check.str_param(daemon_type, "daemon_type")
        return GrapheneDaemonStatus(
            self._instance.get_daemon_statuses(daemon_types=[daemon_type])[daemon_type]
        )

    def resolve_allDaemonStatuses(self, _graphene_info: ResolveInfo):
        return [
            GrapheneDaemonStatus(daemon_status)
            for daemon_status in self._instance.get_daemon_statuses().values()
        ]


class GrapheneClaimedConcurrencySlot(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)

    class Meta:
        name = "ClaimedConcurrencySlot"

    def __init__(self, claimed_slot_info: ClaimedSlotInfo):
        super().__init__(runId=claimed_slot_info.run_id, stepKey=claimed_slot_info.step_key)


class GraphenePendingConcurrencyStep(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)
    stepKey = graphene.NonNull(graphene.String)
    enqueuedTimestamp = graphene.NonNull(graphene.Float)
    assignedTimestamp = graphene.Float()
    priority = graphene.Int()

    class Meta:
        name = "PendingConcurrencyStep"

    def __init__(self, pending_step_info: PendingStepInfo):
        super().__init__(
            runId=pending_step_info.run_id,
            stepKey=pending_step_info.step_key,
            enqueuedTimestamp=pending_step_info.enqueued_timestamp.timestamp(),
            assignedTimestamp=pending_step_info.assigned_timestamp.timestamp()
            if pending_step_info.assigned_timestamp
            else None,
            priority=pending_step_info.priority,
        )


class GrapheneConcurrencyKeyInfo(graphene.ObjectType):
    concurrencyKey = graphene.NonNull(graphene.String)
    slotCount = graphene.NonNull(graphene.Int)
    claimedSlots = non_null_list(GrapheneClaimedConcurrencySlot)
    pendingSteps = non_null_list(GraphenePendingConcurrencyStep)
    activeSlotCount = graphene.NonNull(graphene.Int)
    activeRunIds = non_null_list(graphene.String)
    pendingStepCount = graphene.NonNull(graphene.Int)
    pendingStepRunIds = non_null_list(graphene.String)
    assignedStepCount = graphene.NonNull(graphene.Int)
    assignedStepRunIds = non_null_list(graphene.String)
    limit = graphene.Int()
    usingDefaultLimit = graphene.Boolean()

    class Meta:
        name = "ConcurrencyKeyInfo"

    def __init__(self, concurrency_key: str):
        self._concurrency_key = concurrency_key
        self._concurrency_key_info = None
        super().__init__(concurrencyKey=concurrency_key)

    def _get_concurrency_key_info(self, graphene_info: ResolveInfo):
        if not self._concurrency_key_info:
            self._concurrency_key_info = (
                graphene_info.context.instance.event_log_storage.get_concurrency_info(
                    self._concurrency_key
                )
            )
        return self._concurrency_key_info

    def resolve_claimedSlots(self, graphene_info: ResolveInfo):
        return [
            GrapheneClaimedConcurrencySlot(slot)
            for slot in self._get_concurrency_key_info(graphene_info).claimed_slots
        ]

    def resolve_pendingSteps(self, graphene_info: ResolveInfo):
        return [
            GraphenePendingConcurrencyStep(step)
            for step in self._get_concurrency_key_info(graphene_info).pending_steps
        ]

    def resolve_slotCount(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).slot_count

    def resolve_activeSlotCount(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).active_slot_count

    def resolve_activeRunIds(self, graphene_info: ResolveInfo):
        return list(self._get_concurrency_key_info(graphene_info).active_run_ids)

    def resolve_pendingStepCount(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).pending_step_count

    def resolve_pendingStepRunIds(self, graphene_info: ResolveInfo):
        return list(self._get_concurrency_key_info(graphene_info).pending_run_ids)

    def resolve_assignedStepCount(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).assigned_step_count

    def resolve_assignedStepRunIds(self, graphene_info: ResolveInfo):
        return list(self._get_concurrency_key_info(graphene_info).assigned_run_ids)

    def resolve_limit(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).limit

    def resolve_usingDefaultLimit(self, graphene_info: ResolveInfo):
        return self._get_concurrency_key_info(graphene_info).using_default_limit


class GrapheneRunQueueConfig(graphene.ObjectType):
    maxConcurrentRuns = graphene.NonNull(graphene.Int)
    tagConcurrencyLimitsYaml = graphene.String()
    isOpConcurrencyAware = graphene.Boolean()

    class Meta:
        name = "RunQueueConfig"

    def __init__(self, run_queue_config: "RunQueueConfig"):
        super().__init__()
        self._run_queue_config = run_queue_config

    def resolve_maxConcurrentRuns(self, _graphene_info: ResolveInfo):
        return self._run_queue_config.max_concurrent_runs

    def resolve_tagConcurrencyLimitsYaml(self, _graphene_info: ResolveInfo):
        if not self._run_queue_config.tag_concurrency_limits:
            return None

        return yaml.dump(
            self._run_queue_config.tag_concurrency_limits,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=True,
        )

    def resolve_isOpConcurrencyAware(self, _graphene_info: ResolveInfo):
        return self._run_queue_config.should_block_op_concurrency_limited_runs


class GraphenePoolConfig(graphene.ObjectType):
    poolGranularity = graphene.String()
    defaultPoolLimit = graphene.Int()
    opGranularityRunBuffer = graphene.Int()

    class Meta:
        name = "PoolConfig"

    def __init__(self, pool_config: PoolConfig):
        super().__init__()
        self._pool_config = check.inst_param(pool_config, "pool_config", PoolConfig)

    def resolve_poolGranularity(self, _graphene_info: ResolveInfo):
        return (
            self._pool_config.pool_granularity.value if self._pool_config.pool_granularity else None
        )

    def resolve_defaultPoolLimit(self, _graphene_info: ResolveInfo):
        return self._pool_config.default_pool_limit

    def resolve_opGranularityRunBuffer(self, _graphene_info: ResolveInfo):
        return self._pool_config.op_granularity_run_buffer


class GrapheneInstance(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    info = graphene.Field(graphene.String)
    runLauncher = graphene.Field(GrapheneRunLauncher)
    runQueuingSupported = graphene.NonNull(graphene.Boolean)
    runQueueConfig = graphene.Field(GrapheneRunQueueConfig)
    executablePath = graphene.NonNull(graphene.String)
    daemonHealth = graphene.NonNull(GrapheneDaemonHealth)
    hasInfo = graphene.NonNull(graphene.Boolean)
    autoMaterializePaused = graphene.NonNull(graphene.Boolean)
    supportsConcurrencyLimits = graphene.NonNull(graphene.Boolean)
    minConcurrencyLimitValue = graphene.NonNull(graphene.Int)
    maxConcurrencyLimitValue = graphene.NonNull(graphene.Int)
    concurrencyLimits = non_null_list(GrapheneConcurrencyKeyInfo)
    concurrencyLimit = graphene.Field(
        graphene.NonNull(GrapheneConcurrencyKeyInfo),
        concurrencyKey=graphene.Argument(graphene.String),
    )
    useAutoMaterializeSensors = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        description="Whether or not the deployment is using automation policy sensors to materialize assets",
    )
    poolConfig = graphene.Field(GraphenePoolConfig)

    class Meta:
        name = "Instance"

    def __init__(self, instance):
        super().__init__()
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_id(self, _graphene_info: ResolveInfo):
        return "Instance"

    def resolve_hasInfo(self, graphene_info: ResolveInfo) -> bool:
        return graphene_info.context.show_instance_config

    def resolve_useAutoMaterializeSensors(self, _graphene_info: ResolveInfo):
        return self._instance.auto_materialize_use_sensors

    def resolve_info(self, graphene_info: ResolveInfo):
        return self._instance.info_str() if graphene_info.context.show_instance_config else None

    def resolve_runLauncher(self, _graphene_info: ResolveInfo):
        return (
            GrapheneRunLauncher(self._instance.run_launcher)
            if self._instance.run_launcher
            else None
        )

    def resolve_runQueuingSupported(self, _graphene_info: ResolveInfo):
        from dagster._core.run_coordinator import QueuedRunCoordinator

        return isinstance(self._instance.run_coordinator, QueuedRunCoordinator)

    def resolve_runQueueConfig(self, _graphene_info: ResolveInfo):
        run_queue_config = self._instance.get_concurrency_config().run_queue_config
        if run_queue_config:
            return GrapheneRunQueueConfig(run_queue_config)
        else:
            return None

    def resolve_executablePath(self, _graphene_info: ResolveInfo):
        return sys.executable

    def resolve_daemonHealth(self, _graphene_info: ResolveInfo):
        return GrapheneDaemonHealth(instance=self._instance)

    def resolve_autoMaterializePaused(self, _graphene_info: ResolveInfo):
        return get_auto_materialize_paused(self._instance)

    def resolve_supportsConcurrencyLimits(self, _graphene_info: ResolveInfo):
        return self._instance.event_log_storage.supports_global_concurrency_limits

    def resolve_concurrencyLimits(self, _graphene_info: ResolveInfo):
        res = []
        for key in self._instance.event_log_storage.get_concurrency_keys():
            res.append(GrapheneConcurrencyKeyInfo(key))
        return res

    def resolve_concurrencyLimit(self, _graphene_info: ResolveInfo, concurrencyKey):
        return GrapheneConcurrencyKeyInfo(concurrencyKey)

    def resolve_minConcurrencyLimitValue(self, _graphene_info: ResolveInfo):
        if isinstance(
            self._instance.event_log_storage, SqlEventLogStorage
        ) and not self._instance.event_log_storage.has_table("concurrency_limits"):
            return 1
        return 0

    def resolve_maxConcurrencyLimitValue(self, _graphene_info: ResolveInfo):
        return get_max_concurrency_limit_value()

    def resolve_poolConfig(self, _graphene_info: ResolveInfo):
        concurrency_config = self._instance.get_concurrency_config()
        return GraphenePoolConfig(concurrency_config.pool_config)
