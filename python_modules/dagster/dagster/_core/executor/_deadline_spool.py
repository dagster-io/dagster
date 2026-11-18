"""Ordered file transport for workers with an opt-in lifetime limit."""

import json
import os
import queue
import stat
import time
from pathlib import Path

from dagster._core.events import DagsterEvent
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.error import SerializableErrorInfo

DEFAULT_MAX_EVENT_BYTES = 32 * 1024 * 1024
MAX_PENDING_FRAMES = 128
# Reserved only for the opt-in transport. An explicit user os._exit(73) is
# conservatively treated as transport failure rather than retryable computation.
TRANSPORT_ERROR_EXIT_CODE = 73


class EventTransportError(Exception):
    """Worker event transport failed; retrying user computation cannot repair it."""


class AtomicEventSpool:
    """Single producer and consumer; consumption releases outstanding capacity."""

    def __init__(self, directory: str, max_event_bytes: int = DEFAULT_MAX_EVENT_BYTES):
        self.directory = directory
        self.max_event_bytes = max_event_bytes
        self.write_sequence = 0
        self.read_sequence = 0
        self.failed = False

    def _wait_for_capacity(self, size: int) -> None:
        while True:
            count = total = 0
            for path in Path(self.directory).glob("*.ready"):
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    continue  # The sole consumer removed the committed frame.
                if not stat.S_ISREG(info.st_mode):
                    raise EventTransportError("Invalid worker event file")
                count += 1
                total += info.st_size
            if count < MAX_PENDING_FRAMES and total + size <= self.max_event_bytes:
                return
            time.sleep(0.005)

    def put(self, value) -> None:
        if self.failed:
            raise EventTransportError("Worker event transport previously failed")
        try:
            self._put(value)
        except Exception as exc:
            self.failed = True
            reason = (
                "event_size_limit"
                if isinstance(exc, EventTransportError) and str(exc) == "event_size_limit"
                else "event_transport_failure"
            )
            # A fixed message contains no event data. The dedicated child exit status is
            # authoritative even if a full or unwritable disk prevents this diagnostic.
            try:
                root = Path(self.directory)
                (root / "transport-error.partial").write_text(json.dumps({"reason": reason}))
                os.replace(root / "transport-error.partial", root / "transport-error.json")
            except OSError:
                pass
            raise EventTransportError(reason) from exc

    def _put(self, value) -> None:
        from dagster._core.executor.child_process_executor import (
            ChildProcessDoneEvent,
            ChildProcessStartEvent,
            ChildProcessSystemErrorEvent,
        )

        if isinstance(value, DagsterEvent):
            envelope = {"kind": "event", "value": serialize_value(value)}
        elif isinstance(value, ChildProcessSystemErrorEvent):
            envelope = {
                "kind": "error",
                "pid": value.pid,
                "value": serialize_value(value.error_info),
            }
        elif isinstance(value, (ChildProcessStartEvent, ChildProcessDoneEvent)):
            envelope = {
                "kind": "start" if isinstance(value, ChildProcessStartEvent) else "done",
                "pid": value.pid,
            }
        else:
            raise EventTransportError("Unsupported worker event type")
        data = json.dumps(envelope).encode()
        if len(data) > self.max_event_bytes:
            raise EventTransportError("event_size_limit")
        self._wait_for_capacity(len(data))
        root = Path(self.directory)
        target = root / f"{self.write_sequence:08d}.ready"
        temporary = root / f"{self.write_sequence:08d}.partial"
        with temporary.open("xb") as stream:
            stream.write(data)
        os.replace(temporary, target)
        self.write_sequence += 1

    def get_nowait(self):
        from dagster._core.executor.child_process_executor import (
            ChildProcessDoneEvent,
            ChildProcessStartEvent,
            ChildProcessSystemErrorEvent,
        )

        target = Path(self.directory) / f"{self.read_sequence:08d}.ready"
        try:
            info = target.lstat()
        except FileNotFoundError:
            raise queue.Empty from None
        if not stat.S_ISREG(info.st_mode) or info.st_size > self.max_event_bytes:
            raise EventTransportError("Invalid worker event frame")
        try:
            envelope = json.loads(target.read_bytes())
            kind = envelope.get("kind")
            if kind == "event" and set(envelope) == {"kind", "value"}:
                value = deserialize_value(envelope["value"], DagsterEvent)
            elif (
                kind == "error"
                and set(envelope) == {"kind", "pid", "value"}
                and type(envelope["pid"]) is int
            ):
                value = ChildProcessSystemErrorEvent(
                    envelope["pid"], deserialize_value(envelope["value"], SerializableErrorInfo)
                )
            elif (
                kind in {"start", "done"}
                and set(envelope) == {"kind", "pid"}
                and type(envelope["pid"]) is int
            ):
                value = (ChildProcessStartEvent if kind == "start" else ChildProcessDoneEvent)(
                    envelope["pid"]
                )
            else:
                raise ValueError("Invalid worker event envelope")
        except Exception as exc:
            raise EventTransportError("Invalid worker event frame") from exc
        self.read_sequence += 1
        target.unlink()
        return value

    def close(self):
        pass
