import os
import subprocess

from dagster.core.test_utils import new_cwd
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import wait_for_grpc_server
from dagster.utils import file_relative_path, find_free_port
from dagster.utils.error import SerializableErrorInfo


def test_ping():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")
    process = subprocess.Popen(
        ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        stdout=subprocess.PIPE,
    )

    try:
        assert wait_for_grpc_server(process)
        assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
    finally:
        process.terminate()


def test_load_with_error(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    process = subprocess.Popen(
        ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        stdout=subprocess.PIPE,
    )

    try:
        assert not wait_for_grpc_server(process)
        _, err = capfd.readouterr()
        assert "No module named" in err
    finally:
        process.terminate()


def test_load_with_empty_working_directory():
    port = find_free_port()
    # File that will fail if working directory isn't set to default
    python_file = file_relative_path(__file__, "grpc_repo_with_local_import.py")
    with new_cwd(os.path.dirname(__file__)):
        process = subprocess.Popen(
            ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
            stdout=subprocess.PIPE,
        )

        try:
            assert wait_for_grpc_server(process)
            assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
        finally:
            process.terminate()


def test_lazy_load_with_error():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--lazy-load-user-code",
        ],
        stdout=subprocess.PIPE,
    )

    try:
        assert wait_for_grpc_server(process)
        list_repositories_response = DagsterGrpcClient(port=port).list_repositories()
        assert isinstance(list_repositories_response, SerializableErrorInfo)
        assert "No module named" in list_repositories_response.message
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
