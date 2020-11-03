import sys

import pytest
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import file_relative_path


def test_health_check_success():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        attribute="bar_repo",
        python_file=file_relative_path(__file__, "grpc_repo.py"),
    )
    server = GrpcServerProcess(
        loadable_target_origin=loadable_target_origin,
        max_workers=2,
        heartbeat=True,
        heartbeat_timeout=1,
    )
    with server.create_ephemeral_client() as client:
        assert client.health_check_query() == "SERVING"
    server.wait()


def test_health_check_fail():
    client = DagsterGrpcClient(port=5050)
    with pytest.raises(Exception):
        assert client.health_check_query() == "UNKNOWN"
