import json
import logging

from dagster.core.telemetry import TelemetryRegistry, telemetry_wrapper
from dagster.core.test_utils import instance_for_test


def test_telemetry_instance_logger():
    registry = TelemetryRegistry()

    @telemetry_wrapper(registry=registry)
    def my_func(instance):  # pylint: disable=unused-argument
        pass

    with instance_for_test() as instance:
        my_func(instance)
        telemetry_logger = logging.getLogger("dagster_telemetry_logger")
        path_to_logs = telemetry_logger.handlers[0].baseFilename
        with open(path_to_logs) as f:
            log_string = f.read()
            log_entries = [json.loads(log) for log in log_string.split("\n") if len(log) > 0]

        assert len(log_entries) == 2
        started = log_entries[0]
        assert started["action"] == "my_func_started"
        ended = log_entries[1]
        assert ended["action"] == "my_func_ended"
