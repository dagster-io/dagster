from dagster.daemon.types import DaemonType
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.utils.error import SerializableErrorInfo


def test_error_backcompat():
    old_heartbeat = '{"__class__": "DaemonHeartbeat", "daemon_id": "foobar", "daemon_type": {"__enum__": "DaemonType.SENSOR"}, "error": {"__class__": "SerializableErrorInfo", "cause": null, "cls_name": null, "message": "fizbuz", "stack": []}, "timestamp": 0.0}'
    heartbeat = deserialize_json_to_dagster_namedtuple(old_heartbeat)
    assert heartbeat.daemon_id == "foobar"
    assert heartbeat.daemon_type == DaemonType.SENSOR
    assert heartbeat.timestamp == 0.0
    assert heartbeat.errors == [SerializableErrorInfo("fizbuz", [], None)]
