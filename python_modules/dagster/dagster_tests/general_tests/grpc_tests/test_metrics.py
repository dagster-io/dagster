import inspect
import json
import re
import subprocess
import threading
import time
from typing import Any

import pytest
from dagster._core.host_representation import ExternalRepositoryOrigin
from dagster._core.host_representation.origin import (
    GrpcServerCodeLocationOrigin,
)
from dagster._core.instance import DagsterInstance
from dagster._core.test_utils import (
    instance_for_test,
)
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import (
    METRICS_RETRIEVAL_FUNCTIONS,
    DagsterApiServer,
    wait_for_grpc_server,
)
from dagster._grpc.types import SensorExecutionArgs
from dagster._utils import (
    file_relative_path,
    find_free_port,
)


def is_grpc_method(attr_name: str, obj: Any) -> bool:
    """Grpc methods use pascal casing. This function checks if the given attribute is a method with pascal casing."""
    pascal_case_rgx = re.compile(r"^[A-Z][a-z]*([A-Z][a-z]*)")
    return (
        inspect.isfunction(getattr(obj, attr_name)) and pascal_case_rgx.match(attr_name) is not None
    )


def test_metrics_retrieval_annotations():
    for attr in dir(DagsterApiServer):
        if is_grpc_method(attr, DagsterApiServer):
            if attr != "ExternalSensorExecution":
                continue
            assert attr in METRICS_RETRIEVAL_FUNCTIONS, "Missing annotation for method: " + attr
    for attr in METRICS_RETRIEVAL_FUNCTIONS:
        if attr != "ExternalSensorExecution":
            continue
        assert is_grpc_method(attr, DagsterApiServer), "Missing method for annotation: " + attr


def _launch_sensor_execution(
    repo_origin: ExternalRepositoryOrigin, client: DagsterGrpcClient, instance: DagsterInstance
):
    client.external_sensor_execution(
        sensor_execution_args=SensorExecutionArgs(
            repository_origin=repo_origin,
            instance_ref=instance.get_ref(),
            sensor_name="extremely_slow_sensor",
            last_tick_completion_time=None,
            last_run_key=None,
            cursor=None,
            timeout=2,
            last_sensor_start_time=None,
        ),
    )


@pytest.mark.parametrize("provide_flag", [True, False], ids=["flag-provided", "flag-not-provided"])
def test_ping_metrics_retrieval(provide_flag: bool):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_sensor_eval.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]
    if provide_flag:
        subprocess_args.append("--enable-metrics")

    process = subprocess.Popen(subprocess_args)

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        client = DagsterGrpcClient(port=port)

        with instance_for_test() as instance:
            repo_origin = ExternalRepositoryOrigin(
                code_location_origin=GrpcServerCodeLocationOrigin(port=port, host="localhost"),
                repository_name="the_repo",
            )
            threading.Thread(
                target=_launch_sensor_execution, args=(repo_origin, client, instance)
            ).start()
            time.sleep(2)  # wait for sensor execution to begin
            res = client.ping("blah")
            metadata = json.loads(res["serialized_server_health_metadata"])
            if provide_flag:
                assert "general_info" in metadata
                assert "max_workers" in metadata["general_info"]
                assert metadata["general_info"]["max_workers"] == -1
                assert "SyncExternalSensorExecution" in metadata
                assert metadata["SyncExternalSensorExecution"] == {"current_count": 1}
            else:
                assert metadata == {}
    finally:
        process.terminate()
        process.wait()
