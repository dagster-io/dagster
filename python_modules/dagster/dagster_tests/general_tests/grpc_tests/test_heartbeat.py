import time

from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import file_relative_path


def test_heartbeat():
    loadable_target_origin = LoadableTargetOrigin(
        attribute="bar_repo", python_file=file_relative_path(__file__, "grpc_repo.py"),
    )
    server = GrpcServerProcess(
        loadable_target_origin=loadable_target_origin,
        max_workers=2,
        heartbeat=True,
        heartbeat_timeout=1,
    )
    with server.create_ephemeral_client() as client:
        assert server.server_process.poll() is None

        # heartbeat keeps the server alive
        time.sleep(0.5)
        client.heartbeat()
        time.sleep(0.5)
        client.heartbeat()
        time.sleep(0.5)
        assert server.server_process.poll() is None

        # without the heartbeat, the server dies
        time.sleep(2)
        assert server.server_process.poll() is not None
