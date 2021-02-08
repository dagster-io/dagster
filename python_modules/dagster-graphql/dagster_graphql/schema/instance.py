import sys

import graphene
from dagster import DagsterInstance, check
from dagster.core.launcher.base import RunLauncher
from dagster.daemon.controller import get_daemon_status, required_daemons
from dagster.daemon.types import DaemonStatus

from .errors import GraphenePythonError
from .util import non_null_list


class GrapheneRunLauncher(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)

    class Meta:
        name = "RunLauncher"

    def __init__(self, run_launcher):
        super().__init__()
        self._run_launcher = check.inst_param(run_launcher, "run_launcher", RunLauncher)

    def resolve_name(self, _graphene_info):
        return self._run_launcher.__class__.__name__


class GrapheneDaemonStatus(graphene.ObjectType):
    daemonType = graphene.String()
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
            lastHeartbeatTime=daemon_status.last_heartbeat.timestamp
            if daemon_status.last_heartbeat
            else None,
            lastHeartbeatErrors=[
                GraphenePythonError(error) for error in daemon_status.last_heartbeat.errors
            ]
            if daemon_status.last_heartbeat and daemon_status.last_heartbeat.errors
            else [],
        )

    def resolve_id(self, _graphene_info):
        return self.daemonType


class GrapheneDaemonHealth(graphene.ObjectType):
    daemonStatus = graphene.Field(
        graphene.NonNull(GrapheneDaemonStatus), daemon_type=graphene.Argument(graphene.String)
    )
    allDaemonStatuses = non_null_list(GrapheneDaemonStatus)

    class Meta:
        name = "DaemonHealth"

    def __init__(self, instance):
        super().__init__()
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_daemonStatus(self, _graphene_info, daemon_type):
        check.str_param(daemon_type, "daemon_type")
        return GrapheneDaemonStatus(get_daemon_status(self._instance, daemon_type))

    def resolve_allDaemonStatuses(self, _graphene_info):
        return [
            GrapheneDaemonStatus(get_daemon_status(self._instance, daemon_type))
            for daemon_type in required_daemons(self._instance)
        ]


class GrapheneInstance(graphene.ObjectType):
    info = graphene.NonNull(graphene.String)
    runLauncher = graphene.Field(GrapheneRunLauncher)
    assetsSupported = graphene.NonNull(graphene.Boolean)
    runQueuingSupported = graphene.NonNull(graphene.Boolean)
    executablePath = graphene.NonNull(graphene.String)
    daemonHealth = graphene.NonNull(GrapheneDaemonHealth)

    class Meta:
        name = "Instance"

    def __init__(self, instance):
        super().__init__()
        self._instance = check.inst_param(instance, "instance", DagsterInstance)

    def resolve_info(self, _graphene_info):
        return self._instance.info_str()

    def resolve_runLauncher(self, _graphene_info):
        return (
            GrapheneRunLauncher(self._instance.run_launcher)
            if self._instance.run_launcher
            else None
        )

    def resolve_assetsSupported(self, _graphene_info):
        return self._instance.is_asset_aware

    def resolve_runQueuingSupported(self, _graphene_info):
        from dagster.core.run_coordinator import QueuedRunCoordinator

        return isinstance(self._instance.run_coordinator, QueuedRunCoordinator)

    def resolve_executablePath(self, _graphene_info):
        return sys.executable

    def resolve_daemonHealth(self, _graphene_info):
        return GrapheneDaemonHealth(instance=self._instance)
