from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class DaemonType(Enum):
    # Note: string values are used for serdes in storage
    SENSOR = "SENSOR"
    SCHEDULER = "SCHEDULER"
    QUEUED_RUN_COORDINATOR = "QUEUED_RUN_COORDINATOR"


@whitelist_for_serdes
class DaemonHeartbeat(
    namedtuple("_DaemonHeartbeat", "timestamp daemon_type daemon_id errors error")
):
    """
    Heartbeats are placed in storage by the daemon to show liveness
    """

    def __new__(
        cls, timestamp, daemon_type, daemon_id, errors=None, error=None
    ):  # we need to keep error around forever now in the attr graveyard
        check.opt_inst_param(error, "error", SerializableErrorInfo)
        errors = check.opt_list_param(errors, "errors", of_type=SerializableErrorInfo)
        if error and not errors:
            errors = [error]

        return super(DaemonHeartbeat, cls).__new__(
            cls,
            timestamp=check.float_param(timestamp, "timestamp"),
            daemon_type=check.inst_param(daemon_type, "daemon_type", DaemonType),
            daemon_id=daemon_id,
            errors=errors,
            error=None,
        )


class DaemonStatus(namedtuple("_DaemonStatus", "daemon_type required healthy last_heartbeat")):
    """
    Daemon statuses are derived from daemon heartbeats and instance configuration to provide an
    overview about the daemon's liveness.
    """

    def __new__(cls, daemon_type, required, healthy, last_heartbeat):
        return super(DaemonStatus, cls).__new__(
            cls,
            daemon_type=check.inst_param(daemon_type, "daemon_type", DaemonType),
            required=check.bool_param(required, "required"),
            healthy=check.opt_bool_param(healthy, "healthy"),
            last_heartbeat=check.opt_inst_param(last_heartbeat, "last_heartbeat", DaemonHeartbeat),
        )
