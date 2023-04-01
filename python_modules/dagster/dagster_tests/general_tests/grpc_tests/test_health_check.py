import sys

import pytest
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import GrpcServerProcess
from dagster._utils import file_relative_path


def test_health_check_success():
    with instance_for_test() as instance:
        loadable_target_origin = LoadableTargetOrigin(
            executable_path=sys.executable,
            attribute="bar_repo",
            python_file=file_relative_path(__file__, "grpc_repo.py"),
        )
        with GrpcServerProcess(
            instance_ref=instance.get_ref(),
            loadable_target_origin=loadable_target_origin,
            max_workers=2,
            heartbeat=True,
            heartbeat_timeout=1,
            wait_on_exit=True,
        ) as server:
            client = server.create_client()
            assert client.health_check_query() == "SERVING"


def test_health_check_fail():
    client = DagsterGrpcClient(port=5050)
    with pytest.raises(Exception):
        assert client.health_check_query() == "UNKNOWN"
