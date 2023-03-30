from typing import Any, Dict, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import (
    BottomUpUnpackContext,
    NamedTupleSerializer,
    UnknownSerdesValue,
    is_packed_enum,
)
from dagster._utils.error import SerializableErrorInfo


class DaemonHeartbeatSerializer(NamedTupleSerializer["DaemonHeartbeat"]):
    def before_unpack(self, context, storage_dict: Dict[str, Any]):
        # Previously daemon types were enums, now they are strings. If we find a packed enum,
        # just extract the name, which is the string we want.

        if is_packed_enum(storage_dict.get("daemon_type")):
            storage_dict["daemon_type"] = storage_dict["daemon_type"]["__enum__"].split(".")[-1]
        elif isinstance(storage_dict.get("daemon_type"), UnknownSerdesValue):
            if not isinstance(context, BottomUpUnpackContext):
                check.failed(f"Unexpected state, got UnknownSerdesValue with context {context}")
            unknown = storage_dict["daemon_type"]
            storage_dict["daemon_type"] = unknown.value["__enum__"].split(".")[-1]
            context.clear_ignored_unknown_values(unknown)

        if storage_dict.get("error"):
            storage_dict["errors"] = [storage_dict["error"]]
            del storage_dict["error"]
        return storage_dict


@whitelist_for_serdes(serializer=DaemonHeartbeatSerializer)
class DaemonHeartbeat(
    NamedTuple(
        "_DaemonHeartbeat",
        [
            ("timestamp", float),
            ("daemon_type", str),
            ("daemon_id", Optional[str]),
            ("errors", Optional[Sequence[SerializableErrorInfo]]),
        ],
    ),
):
    def __new__(
        cls,
        timestamp: float,
        daemon_type: str,
        daemon_id: Optional[str],
        errors: Optional[Sequence[SerializableErrorInfo]] = None,
    ):
        errors = check.opt_sequence_param(errors, "errors", of_type=SerializableErrorInfo)

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
    """Daemon statuses are derived from daemon heartbeats and instance configuration to provide an
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
