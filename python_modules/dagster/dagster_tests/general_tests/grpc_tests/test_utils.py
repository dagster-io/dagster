from dagster._core.test_utils import environ
from dagster._grpc.utils import (
    default_grpc_server_shutdown_grace_period,
    default_grpc_timeout,
    default_schedule_grpc_timeout,
    default_sensor_grpc_timeout,
)


def test_default_grpc_timeouts():
    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 60
        assert default_sensor_grpc_timeout() == 60
        assert default_grpc_server_shutdown_grace_period() == 60


def test_override_grpc_timeouts():
    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": "120",
        }
    ):
        assert default_grpc_timeout() == 120
        assert default_schedule_grpc_timeout() == 120
        assert default_sensor_grpc_timeout() == 120
        assert default_grpc_server_shutdown_grace_period() == 120

    with environ(
        {
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": "45",
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 45
        assert default_sensor_grpc_timeout() == 60
        assert default_grpc_server_shutdown_grace_period() == 60

    with environ(
        {
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": "45",
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 60
        assert default_sensor_grpc_timeout() == 45
        assert default_grpc_server_shutdown_grace_period() == 60

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": "75",
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": "120",
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": "400",
        }
    ):
        assert default_grpc_timeout() == 75
        assert default_schedule_grpc_timeout() == 120
        assert default_sensor_grpc_timeout() == 400
        assert default_grpc_server_shutdown_grace_period() == 400
