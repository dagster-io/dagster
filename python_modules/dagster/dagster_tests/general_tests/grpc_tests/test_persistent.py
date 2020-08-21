import subprocess

from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import wait_for_grpc_server
from dagster.utils import file_relative_path, find_free_port


def test_ping():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")
    process = subprocess.Popen(
        ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process)
        assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
    finally:
        process.terminate()


def test_streaming():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")
    process = subprocess.Popen(
        ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process)
        api_client = DagsterGrpcClient(port=port)
        results = [result for result in api_client.streaming_ping(sequence_length=10, echo="foo")]
        assert len(results) == 10
        for sequence_number, result in enumerate(results):
            assert result["sequence_number"] == sequence_number
            assert result["echo"] == "foo"
    finally:
        process.terminate()
