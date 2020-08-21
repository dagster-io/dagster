import sys
from collections import namedtuple

from dagster.serdes import whitelist_for_serdes
from dagster.serdes.ipc import IPCErrorMessage, ipc_read_event_stream, ipc_write_stream
from dagster.utils import safe_tempfile_path


def test_write_read_stream():
    @whitelist_for_serdes
    class TestMessage(namedtuple("_TestMessage", "message")):
        def __new__(cls, message):
            return super(TestMessage, cls).__new__(cls, message)

    with safe_tempfile_path() as f:
        message_1 = TestMessage(message="hello")
        message_2 = TestMessage(message="world")

        with ipc_write_stream(f) as stream:
            stream.send(message_1)
            stream.send(message_2)

        messages = []
        for message in ipc_read_event_stream(f):
            messages.append(message)

        assert messages[0] == message_1
        assert messages[1] == message_2


def test_write_empty_stream():

    with safe_tempfile_path() as f:
        with ipc_write_stream(f) as _:
            pass

        messages = []
        for message in ipc_read_event_stream(f):
            messages.append(message)

        assert len(messages) == 0


def test_write_error_stream():
    with safe_tempfile_path() as filename:
        with ipc_write_stream(filename) as _:
            raise Exception("uh oh")

        messages = []
        for message in ipc_read_event_stream(filename):
            messages.append(message)

        assert len(messages) == 1
        message = messages[0]

        assert isinstance(message, IPCErrorMessage)
        assert "uh oh" in message.serializable_error_info.message


def test_write_error_with_custom_message():
    with safe_tempfile_path() as filename:
        with ipc_write_stream(filename) as stream:
            try:
                raise Exception("uh oh")
            except:  # pylint: disable=bare-except
                stream.send_error(sys.exc_info(), message="custom")

        messages = []
        for message in ipc_read_event_stream(filename):
            messages.append(message)

        assert len(messages) == 1
        ipc_message = messages[0]

        assert isinstance(ipc_message, IPCErrorMessage)
        assert "uh oh" in ipc_message.serializable_error_info.message
        assert ipc_message.message == "custom"
