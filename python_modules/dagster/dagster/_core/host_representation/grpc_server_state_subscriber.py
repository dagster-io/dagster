from enum import Enum
from typing import NamedTuple, Optional

import dagster._check as check


class LocationStateChangeEventType(Enum):
    LOCATION_UPDATED = "LOCATION_UPDATED"
    LOCATION_DISCONNECTED = "LOCATION_DISCONNECTED"
    LOCATION_RECONNECTED = "LOCATION_RECONNECTED"
    LOCATION_ERROR = "LOCATION_ERROR"


class LocationStateChangeEvent(
    NamedTuple(
        "_LocationStateChangeEvent",
        [
            ("event_type", LocationStateChangeEventType),
            ("location_name", str),
            ("message", str),
            ("server_id", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        event_type: LocationStateChangeEventType,
        location_name: str,
        message: str,
        server_id: Optional[str] = None,
    ):
        return super(LocationStateChangeEvent, cls).__new__(
            cls,
            check.inst_param(event_type, "event_type", LocationStateChangeEventType),
            check.str_param(location_name, "location_name"),
            check.str_param(message, "message"),
            check.opt_str_param(server_id, "server_id"),
        )


class LocationStateSubscriber:
    def __init__(self, callback):
        check.callable_param(callback, "callback")
        self._callback = callback

    def handle_event(self, event):
        check.inst_param(event, "event", LocationStateChangeEvent)
        self._callback(event)
