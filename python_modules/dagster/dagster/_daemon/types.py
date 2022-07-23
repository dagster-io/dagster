from enum import Enum
from typing import List, NamedTuple, Optional, cast

import dagster._check as check
from dagster._serdes import DefaultNamedTupleSerializer, unpack_inner_value, whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo


# DEPRECATED - daemon types are now strings, only exists in code for deserializing old heartbeats
@whitelist_for_serdes
class DaemonType(Enum):
    SENSOR = "SENSOR"
    SCHEDULER = "SCHEDULER"
    QUEUED_RUN_COORDINATOR = "QUEUED_RUN_COORDINATOR"


class DaemonBackcompat(DefaultNamedTupleSerializer):
    @classmethod
    def value_from_storage_dict(
        cls,
        storage_dict,
        klass,
        args_for_class,
        whitelist_map,
        descent_path,
    ):
        # Handle case where daemon_type used to be an enum (e.g. DaemonType.SCHEDULER)
        daemon_type = unpack_inner_value(
            storage_dict.get("daemon_type"),
            whitelist_map,
            descent_path=f"{descent_path}.daemon_type",
        )
        return DaemonHeartbeat(
            timestamp=cast(float, storage_dict.get("timestamp")),
            daemon_type=(daemon_type.value if isinstance(daemon_type, DaemonType) else daemon_type),
            daemon_id=cast(str, storage_dict.get("daemon_id")),
            errors=[
                unpack_inner_value(
                    storage_dict.get("error"),
                    whitelist_map,
                    descent_path=f"{descent_path}.error",
                )
            ]  # error was replaced with errors
            if storage_dict.get("error")
            else unpack_inner_value(
                storage_dict.get("errors"),
                whitelist_map,
                descent_path=f"{descent_path}.errors",
            ),
        )


@whitelist_for_serdes(serializer=DaemonBackcompat)
class DaemonHeartbeat(
    NamedTuple(
        "_DaemonHeartbeat",
        [
            ("timestamp", float),
            ("daemon_type", str),
            ("daemon_id", Optional[str]),
            ("errors", Optional[List[SerializableErrorInfo]]),
        ],
    ),
):
    def __new__(
        cls,
        timestamp: float,
        daemon_type: str,
        daemon_id: str,
        errors: Optional[List[SerializableErrorInfo]] = None,
    ):
        errors = check.opt_list_param(errors, "errors", of_type=SerializableErrorInfo)

        return super(DaemonHeartbeat, cls).__new__(
            cls,
            timestamp=check.float_param(timestamp, "timestamp"),
            daemon_type=check.str_param(daemon_type, "daemon_type"),
            daemon_id=check.opt_str_param(daemon_id, "daemon_id"),
            errors=errors,
        )


class DaemonStatus(
    NamedTuple(
        "_DaemonStatus",
        [
            ("daemon_type", str),
            ("required", bool),
            ("healthy", Optional[bool]),
            ("last_heartbeat", Optional[DaemonHeartbeat]),
        ],
    )
):
    """
    Daemon statuses are derived from daemon heartbeats and instance configuration to provide an
    overview about the daemon's liveness.
    """

    def __new__(
        cls,
        daemon_type: str,
        required: bool,
        healthy: Optional[bool],
        last_heartbeat: Optional[DaemonHeartbeat],
    ):
        return super(DaemonStatus, cls).__new__(
            cls,
            daemon_type=check.str_param(daemon_type, "daemon_type"),
            required=check.bool_param(required, "required"),
            healthy=check.opt_bool_param(healthy, "healthy"),
            last_heartbeat=check.opt_inst_param(last_heartbeat, "last_heartbeat", DaemonHeartbeat),
        )
