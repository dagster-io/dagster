from dagster.core.definitions.run_status_sensor_definition import RunStatusSensorCursor
from dagster.daemon.types import DaemonHeartbeat
from dagster.serdes import deserialize_as, deserialize_json_to_dagster_namedtuple
from dagster.utils.error import SerializableErrorInfo


def test_error_backcompat():
    old_heartbeat = '{"__class__": "DaemonHeartbeat", "daemon_id": "foobar", "daemon_type": {"__enum__": "DaemonType.SENSOR"}, "error": {"__class__": "SerializableErrorInfo", "cause": null, "cls_name": null, "message": "fizbuz", "stack": []}, "timestamp": 0.0}'
    heartbeat = deserialize_as(old_heartbeat, DaemonHeartbeat)
    assert heartbeat.daemon_id == "foobar"
    assert heartbeat.daemon_type == "SENSOR"
    assert heartbeat.timestamp == 0.0
    assert heartbeat.errors == [SerializableErrorInfo("fizbuz", [], None)]


def test_heartbeat_backcompat():
    old_heartbeat = '{"__class__": "DaemonHeartbeat", "daemon_id": "05f24887-fb6a-4821-807b-fbd772a921e3", "daemon_type": {"__enum__": "DaemonType.SCHEDULER"}, "errors": [], "timestamp": 1612453213.775866}'
    heartbeat = deserialize_as(old_heartbeat, DaemonHeartbeat)
    assert heartbeat.daemon_id == "05f24887-fb6a-4821-807b-fbd772a921e3"
    assert heartbeat.daemon_type == "SCHEDULER"
    assert heartbeat.errors == []
    assert heartbeat.timestamp == 1612453213.775866


def test_run_status_sensor_cursor_backcompat():
    old_cursor = '{"__class__": "PipelineSensorCursor", "record_id": 20585, "update_timestamp": "2021-07-22T00:22:29.914776+00:00"}'
    assert RunStatusSensorCursor.is_valid(old_cursor)
    cursor = deserialize_json_to_dagster_namedtuple(old_cursor)
    assert isinstance(cursor, RunStatusSensorCursor)
    assert cursor.record_id == 20585
