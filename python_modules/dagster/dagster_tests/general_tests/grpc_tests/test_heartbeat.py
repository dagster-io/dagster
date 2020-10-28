import sys
import time

from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.server import GrpcServerProcess
from dagster.utils import file_relative_path


def test_heartbeat():
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
        assert server.server_process.poll() is None

        # heartbeat keeps the server alive
        time.sleep(0.5)
        client.heartbeat()
        time.sleep(0.5)
        client.heartbeat()
        time.sleep(0.5)
        assert server.server_process.poll() is None

        start_time = time.time()
        while (time.time() - start_time) < 10:
            if server.server_process.poll() is not None:
                return
            time.sleep(0.1)

        raise Exception("Timed out waiting for server to terminate after heartbeat stopped")
