import json
import logging
import time
from contextlib import contextmanager

from dagster.core.telemetry import TelemetryRegistry, telemetry_wrapper
from dagster.core.test_utils import instance_for_test

registry_for_test = TelemetryRegistry()


@telemetry_wrapper(registry=registry_for_test)
def my_func(instance):  # pylint: disable=unused-argument
    pass


def test_telemetry_instance_logger():

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


class RecordMethodTelemetry:
    @telemetry_wrapper(registry=registry_for_test)
    def my_meth(self, instance):  # pylint: disable=unused-argument
        pass


def test_telemetry_on_class_method():
    assert "RecordMethodTelemetry.my_meth" in list(registry_for_test.registry.keys())

    with instance_for_test() as instance:
        RecordMethodTelemetry().my_meth(instance)
        telemetry_logger = logging.getLogger("dagster_telemetry_logger")
        path_to_logs = telemetry_logger.handlers[0].baseFilename
        with open(path_to_logs) as f:
            log_string = f.read()
            log_entries = [json.loads(log) for log in log_string.split("\n") if len(log) > 0]

        assert len(log_entries) == 2
        started = log_entries[0]
        assert started["action"] == "RecordMethodTelemetry.my_meth_started"
        ended = log_entries[1]
        assert ended["action"] == "RecordMethodTelemetry.my_meth_ended"


@contextmanager
@telemetry_wrapper(registry=registry_for_test)
def dummy_cm(instance):  # pylint: disable=unused-argument
    time.sleep(1)
    yield "foo"


def test_telemetry_on_contextmanager():
    assert "dummy_cm" in list(registry_for_test.registry.keys())

    with instance_for_test() as instance:
        with dummy_cm(instance):
            pass
        telemetry_logger = logging.getLogger("dagster_telemetry_logger")
        path_to_logs = telemetry_logger.handlers[0].baseFilename
        with open(path_to_logs) as f:
            log_string = f.read()
            log_entries = [json.loads(log) for log in log_string.split("\n") if len(log) > 0]

        assert len(log_entries) == 2
        started = log_entries[0]
        assert started["action"] == "dummy_cm_started"
        ended = log_entries[1]
        assert ended["action"] == "dummy_cm_ended"

        # Ensure that the sleep is accounted for in the last time and we track how long the
        # generator takes to yield all results.
        assert ended["elapsed_time"] > "0:00:01"
