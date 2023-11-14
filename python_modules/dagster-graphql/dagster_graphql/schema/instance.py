import sys

import dagster._check as check
import graphene
from dagster._core.instance import DagsterInstance
from dagster._core.launcher.base import RunLauncher
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._daemon.asset_daemon import get_auto_materialize_paused
from dagster._daemon.types import DaemonStatus
from dagster._utils.concurrency import ClaimedSlotInfo, ConcurrencyKeyInfo, PendingStepInfo

from .errors import GraphenePythonError
from .util import ResolveInfo, non_null_list


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
        graphene.NonNull(GrapheneDaemonStatus), daemon_type=graphene.Argument(graphene.String)
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

    class Meta:
        name = "ConcurrencyKeyInfo"

    def __init__(self, concurrency_key_info: ConcurrencyKeyInfo):
        self._claimed_slots = concurrency_key_info.claimed_slots
        self._pending_steps = concurrency_key_info.pending_steps
        super().__init__(
            concurrencyKey=concurrency_key_info.concurrency_key,
            slotCount=concurrency_key_info.slot_count,
            activeSlotCount=concurrency_key_info.active_slot_count,
            activeRunIds=list(concurrency_key_info.active_run_ids),
            pendingStepCount=concurrency_key_info.pending_step_count,
            pendingStepRunIds=list(concurrency_key_info.pending_run_ids),
            assignedStepCount=concurrency_key_info.assigned_step_count,
            assignedStepRunIds=list(concurrency_key_info.assigned_run_ids),
        )

    def resolve_claimedSlots(self, _graphene_info: ResolveInfo):
        return [GrapheneClaimedConcurrencySlot(slot) for slot in self._claimed_slots]

    def resolve_pendingSteps(self, _graphene_info: ResolveInfo):
        return [GraphenePendingConcurrencyStep(step) for step in self._pending_steps]


class GrapheneInstance(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    info = graphene.Field(graphene.String)
    runLauncher = graphene.Field(GrapheneRunLauncher)
    runQueuingSupported = graphene.NonNull(graphene.Boolean)
    executablePath = graphene.NonNull(graphene.String)
    daemonHealth = graphene.NonNull(GrapheneDaemonHealth)
    hasInfo = graphene.NonNull(graphene.Boolean)
    hasCapturedLogManager = graphene.NonNull(graphene.Boolean)
    autoMaterializePaused = graphene.NonNull(graphene.Boolean)
    supportsConcurrencyLimits = graphene.NonNull(graphene.Boolean)
    concurrencyLimits = non_null_list(GrapheneConcurrencyKeyInfo)

    class Meta:
        name = "Instance"

    def __init__(self, instance):
        super().__init__()
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_id(self, _graphene_info: ResolveInfo):
        return "Instance"

    def resolve_hasInfo(self, graphene_info: ResolveInfo) -> bool:
        return graphene_info.context.show_instance_config

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

    def resolve_executablePath(self, _graphene_info: ResolveInfo):
        return sys.executable

    def resolve_daemonHealth(self, _graphene_info: ResolveInfo):
        return GrapheneDaemonHealth(instance=self._instance)

    def resolve_hasCapturedLogManager(self, _graphene_info: ResolveInfo):
        return isinstance(self._instance.compute_log_manager, CapturedLogManager)

    def resolve_autoMaterializePaused(self, _graphene_info: ResolveInfo):
        return get_auto_materialize_paused(self._instance)

    def resolve_supportsConcurrencyLimits(self, _graphene_info: ResolveInfo):
        return self._instance.event_log_storage.supports_global_concurrency_limits

    def resolve_concurrencyLimits(self, _graphene_info: ResolveInfo):
        res = []
        for key in self._instance.event_log_storage.get_concurrency_keys():
            key_info = self._instance.event_log_storage.get_concurrency_info(key)
            res.append(GrapheneConcurrencyKeyInfo(key_info))
        return res
