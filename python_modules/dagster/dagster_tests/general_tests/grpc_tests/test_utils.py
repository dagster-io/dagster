from dagster._core.test_utils import environ
from dagster._grpc.utils import (
    default_grpc_server_shutdown_grace_period,
    default_grpc_timeout,
    default_repository_grpc_timeout,
    default_schedule_grpc_timeout,
    default_sensor_grpc_timeout,
)


def test_default_grpc_timeouts():
    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 60
        assert default_sensor_grpc_timeout() == 60
        assert default_grpc_server_shutdown_grace_period() == 60
        assert default_repository_grpc_timeout() == 180


def test_override_grpc_timeouts():
    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": "120",
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 120
        assert default_schedule_grpc_timeout() == 120
        assert default_sensor_grpc_timeout() == 120
        assert default_grpc_server_shutdown_grace_period() == 120
        assert default_repository_grpc_timeout() == 180

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": "240",
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 240
        assert default_schedule_grpc_timeout() == 240
        assert default_sensor_grpc_timeout() == 240
        assert default_grpc_server_shutdown_grace_period() == 240
        assert default_repository_grpc_timeout() == 240

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": "45",
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 45
        assert default_sensor_grpc_timeout() == 60
        assert default_grpc_server_shutdown_grace_period() == 60
        assert default_repository_grpc_timeout() == 180

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": "45",
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 60
        assert default_sensor_grpc_timeout() == 45
        assert default_repository_grpc_timeout() == 180
        assert default_grpc_server_shutdown_grace_period() == 60

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": "75",
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": "120",
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": "400",
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": None,
        }
    ):
        assert default_grpc_timeout() == 75
        assert default_schedule_grpc_timeout() == 120
        assert default_sensor_grpc_timeout() == 400
        assert default_repository_grpc_timeout() == 180
        assert default_grpc_server_shutdown_grace_period() == 400

    with environ(
        {
            "DAGSTER_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SCHEDULE_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_SENSOR_GRPC_TIMEOUT_SECONDS": None,
            "DAGSTER_REPOSITORY_GRPC_TIMEOUT_SECONDS": "300",
        }
    ):
        assert default_grpc_timeout() == 60
        assert default_schedule_grpc_timeout() == 60
        assert default_sensor_grpc_timeout() == 60
        assert default_grpc_server_shutdown_grace_period() == 60
        assert default_repository_grpc_timeout() == 300
