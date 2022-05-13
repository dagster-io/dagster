import os
import signal
import subprocess
import sys
from contextlib import contextmanager
from time import sleep
from typing import NamedTuple, Optional

import dagster._check as check
from dagster.core.errors import DagsterError
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def write_unary_input(input_file, obj):
    check.str_param(input_file, "input_file")
    check.not_none_param(obj, "obj")
    with open(os.path.abspath(input_file), "w", encoding="utf8") as fp:
        fp.write(serialize_dagster_namedtuple(obj))


def read_unary_input(input_file):
    check.str_param(input_file, "input_file")
    with open(os.path.abspath(input_file), "r", encoding="utf8") as fp:
        return deserialize_json_to_dagster_namedtuple(fp.read())


def ipc_write_unary_response(output_file, obj):
    check.not_none_param(obj, "obj")
    with ipc_write_stream(output_file) as stream:
        stream.send(obj)


def read_unary_response(output_file, timeout=30, ipc_process=None):
    messages = list(ipc_read_event_stream(output_file, timeout=timeout, ipc_process=ipc_process))
    check.invariant(len(messages) == 1)
    return messages[0]


@whitelist_for_serdes
class IPCStartMessage(NamedTuple("_IPCStartMessage", [])):
    def __new__(cls):
        return super(IPCStartMessage, cls).__new__(cls)


@whitelist_for_serdes
class IPCErrorMessage(
    NamedTuple(
        "_IPCErrorMessage",
        [("serializable_error_info", SerializableErrorInfo), ("message", Optional[str])],
    )
):
    """
    This represents a user error encountered during the IPC call. This indicates a business
    logic error, rather than a protocol. Consider this a "task failed successfully"
    use case.
    """

    def __new__(cls, serializable_error_info: SerializableErrorInfo, message: Optional[str]):
        return super(IPCErrorMessage, cls).__new__(
            cls,
            serializable_error_info=check.inst_param(
                serializable_error_info, "serializable_error_info", SerializableErrorInfo
            ),
            message=check.opt_str_param(message, "message"),
        )


@whitelist_for_serdes
class IPCEndMessage(NamedTuple("_IPCEndMessage", [])):
    def __new__(cls):
        return super(IPCEndMessage, cls).__new__(cls)


class DagsterIPCProtocolError(DagsterError):
    """
    This indicates that something went wrong with the protocol. E.g. the
    process being called did not emit an IPCStartMessage first.
    """

    def __init__(self, message):
        self.message = message
        super(DagsterIPCProtocolError, self).__init__(message)


class FileBasedWriteStream:
    def __init__(self, file_path):
        check.str_param("file_path", file_path)
        self._file_path = file_path

    def send(self, dagster_named_tuple):
        _send(self._file_path, dagster_named_tuple)

    def send_error(self, exc_info, message=None):
        _send_error(self._file_path, exc_info, message=message)


def _send(file_path, obj):
    with open(os.path.abspath(file_path), "a+", encoding="utf8") as fp:
        fp.write(serialize_dagster_namedtuple(obj) + "\n")


def _send_error(file_path, exc_info, message):
    return _send(
        file_path,
        IPCErrorMessage(
            serializable_error_info=serializable_error_info_from_exc_info(exc_info), message=message
        ),
    )


@contextmanager
def ipc_write_stream(file_path):
    check.str_param("file_path", file_path)
    _send(file_path, IPCStartMessage())
    try:
        yield FileBasedWriteStream(file_path)
    except Exception:
        _send_error(file_path, sys.exc_info(), message=None)
    finally:
        _send(file_path, IPCEndMessage())


def _process_line(file_pointer, sleep_interval=0.1):
    while True:
        line = file_pointer.readline()
        if line:
            return deserialize_json_to_dagster_namedtuple(line.rstrip())
        sleep(sleep_interval)


def _poll_process(ipc_process):
    if not ipc_process:
        return
    if ipc_process.poll() != None:
        raise DagsterIPCProtocolError(
            "Process exited with return code {return_code} while waiting for events".format(
                return_code=ipc_process.returncode
            )
        )


def ipc_read_event_stream(file_path, timeout=30, ipc_process=None):
    # Wait for file to be ready
    sleep_interval = 0.1
    elapsed_time = 0
    while elapsed_time < timeout and not os.path.exists(file_path):
        _poll_process(ipc_process)
        elapsed_time += sleep_interval
        sleep(sleep_interval)

    if not os.path.exists(file_path):
        raise DagsterIPCProtocolError(
            "Timeout: read stream has not received any data in {timeout} seconds".format(
                timeout=timeout
            )
        )

    with open(os.path.abspath(file_path), "r", encoding="utf8") as file_pointer:
        message = _process_line(file_pointer)
        while elapsed_time < timeout and message == None:
            _poll_process(ipc_process)
            elapsed_time += sleep_interval
            sleep(sleep_interval)
            message = _process_line(file_pointer)

        # Process start message
        if not isinstance(message, IPCStartMessage):
            raise DagsterIPCProtocolError(
                "Attempted to read stream at file {file_path}, but first message was not an "
                "IPCStartMessage".format(file_path=file_path)
            )

        message = _process_line(file_pointer)
        while not isinstance(message, IPCEndMessage):
            if message == None:
                _poll_process(ipc_process)
            yield message
            message = _process_line(file_pointer)


# Windows subprocess termination utilities
# https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/


def open_ipc_subprocess(parts, **kwargs):
    """Sets new process group flags on Windows to support graceful termination."""
    check.list_param(parts, "parts", str)

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(parts, creationflags=creationflags, **kwargs)


def interrupt_ipc_subprocess(proc):
    """Send CTRL_BREAK on Windows, SIGINT on other platforms"""

    if sys.platform == "win32":
        proc.send_signal(signal.CTRL_BREAK_EVENT)  # pylint: disable=no-member
    else:
        proc.send_signal(signal.SIGINT)


def interrupt_ipc_subprocess_pid(pid):
    """Send CTRL_BREAK on Windows, SIGINT on other platforms"""
    check.int_param(pid, "pid")

    if sys.platform == "win32":
        os.kill(pid, signal.CTRL_BREAK_EVENT)  # pylint: disable=no-member
    else:
        os.kill(pid, signal.SIGINT)
