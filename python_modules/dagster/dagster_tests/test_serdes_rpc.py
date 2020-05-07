import tempfile
from collections import namedtuple

from dagster.serdes import whitelist_for_serdes
from dagster.serdes.ipc import ipc_read_event_stream, ipc_write_stream


def test_write_read_stream():
    @whitelist_for_serdes
    class TestMessage(namedtuple('_TestMessage', 'message')):
        def __new__(cls, message):
            return super(TestMessage, cls).__new__(cls, message)

    with tempfile.NamedTemporaryFile() as f:
        message_1 = TestMessage(message="hello")
        message_2 = TestMessage(message="world")

        with ipc_write_stream(f.name) as stream:
            stream.send(message_1)
            stream.send(message_2)

        messages = []
        for message in ipc_read_event_stream(f.name):
            messages.append(message)

        assert messages[0] == message_1
        assert messages[1] == message_2


def test_write_empty_stream():

    with tempfile.NamedTemporaryFile() as f:
        with ipc_write_stream(f.name) as _:
            pass

        messages = []
        for message in ipc_read_event_stream(f.name):
            messages.append(message)

        assert len(messages) == 0
