from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.serdes import DefaultNamedTupleSerializer, unpack_value, whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


# DEPRECATED - daemon types are now strings, only exists in code for deserializing old heartbeats
@whitelist_for_serdes
class DaemonType(Enum):
    SENSOR = "SENSOR"
    SCHEDULER = "SCHEDULER"
    QUEUED_RUN_COORDINATOR = "QUEUED_RUN_COORDINATOR"


class DaemonBackcompat(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(cls, storage_dict, klass):
        # Handle case where daemon_type used to be an enum (e.g. DaemonType.SCHEDULER)
        return DaemonHeartbeat(
            timestamp=storage_dict.get("timestamp"),
            daemon_type=(
                storage_dict.get("daemon_type").value
                if isinstance(storage_dict.get("daemon_type"), DaemonType)
                else storage_dict.get("daemon_type")
            ),
            daemon_id=storage_dict.get("daemon_id"),
            errors=[unpack_value(storage_dict.get("error"))]  # error was replaced with errors
            if storage_dict.get("error")
            else unpack_value(storage_dict.get("errors")),
        )


@whitelist_for_serdes(serializer=DaemonBackcompat)
class DaemonHeartbeat(
    namedtuple("_DaemonHeartbeat", "timestamp daemon_type daemon_id errors"),
):
    def __new__(cls, timestamp, daemon_type, daemon_id, errors=None):
        errors = check.opt_list_param(errors, "errors", of_type=SerializableErrorInfo)

        return super(DaemonHeartbeat, cls).__new__(
            cls,
            timestamp=check.float_param(timestamp, "timestamp"),
            daemon_type=check.str_param(daemon_type, "daemon_type"),
            daemon_id=daemon_id,
            errors=errors,
        )


class DaemonStatus(namedtuple("_DaemonStatus", "daemon_type required healthy last_heartbeat")):
    """
    Daemon statuses are derived from daemon heartbeats and instance configuration to provide an
    overview about the daemon's liveness.
    """

    def __new__(cls, daemon_type, required, healthy, last_heartbeat):
        return super(DaemonStatus, cls).__new__(
            cls,
            daemon_type=check.str_param(daemon_type, "daemon_type"),
            required=check.bool_param(required, "required"),
            healthy=check.opt_bool_param(healthy, "healthy"),
            last_heartbeat=check.opt_inst_param(last_heartbeat, "last_heartbeat", DaemonHeartbeat),
        )
