import os
import re
import subprocess
import uuid

import pytest
from dagster import seven
from dagster.core.host_representation.origin import (
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocationOrigin,
)
from dagster.core.test_utils import environ, instance_for_test, new_cwd
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import wait_for_grpc_server
from dagster.grpc.types import SensorExecutionArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple
from dagster.seven import get_system_temp_directory
from dagster.utils import file_relative_path, find_free_port
from dagster.utils.error import SerializableErrorInfo


def _get_ipc_output_file():
    return os.path.join(
        get_system_temp_directory(), "grpc-server-startup-{uuid}".format(uuid=uuid.uuid4().hex)
    )


def test_ping():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(subprocess_args, stdout=subprocess.PIPE)

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"

        subprocess.check_call(["dagster", "api", "grpc-health-check", "--port", str(port)])

        ssl_result = subprocess.run(  # pylint:disable=subprocess-run-check
            ["dagster", "api", "grpc-health-check", "--port", str(port), "--use-ssl"]
        )
        assert ssl_result.returncode == 1

    finally:
        process.terminate()


def test_load_via_env_var():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--python-file",
        python_file,
    ]

    with environ(
        {"DAGSTER_CLI_API_GRPC_HOST": "localhost", "DAGSTER_CLI_API_GRPC_PORT": str(port)}
    ):
        process = subprocess.Popen(
            subprocess_args,
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
        finally:
            process.terminate()


def test_load_with_invalid_param(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--foo-param",
        "bar_value",
    ]

    process = subprocess.Popen(
        subprocess_args,
        stdout=subprocess.PIPE,
    )

    try:
        with pytest.raises(
            Exception,
            match='gRPC server exited with return code 2 while starting up with the command: "dagster api grpc --port',
        ):
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
    finally:
        process.terminate()

    _, err = capfd.readouterr()

    assert "no such option" in err.lower()


def test_load_with_error(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(
        subprocess_args,
        stdout=subprocess.PIPE,
    )

    try:
        with pytest.raises(Exception):
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
        process.wait()

        _, err = capfd.readouterr()
        assert "No module named" in err
    finally:
        if process.poll() is None:
            process.terminate()


def test_load_with_non_existant_file(capfd):
    port = find_free_port()
    # File that will fail if working directory isn't set to default
    python_file = file_relative_path(__file__, "made_up_file_does_not_exist.py")

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_output(
            ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        )

    _, err = capfd.readouterr()

    if seven.IS_WINDOWS:
        assert "The system cannot find the file specified" in err
    else:
        assert "No such file or directory" in err


def test_load_with_empty_working_directory(capfd):
    port = find_free_port()
    # File that will fail if working directory isn't set to default
    python_file = file_relative_path(__file__, "grpc_repo_with_local_import.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    with new_cwd(os.path.dirname(__file__)):
        process = subprocess.Popen(
            subprocess_args,
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
        finally:
            process.terminate()

        # indicating the working directory is empty fails

        port = find_free_port()
        subprocess_args = [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--empty-working-directory",
        ]

        process = subprocess.Popen(
            subprocess_args,
            stdout=subprocess.PIPE,
        )
        try:
            with pytest.raises(Exception):
                wait_for_grpc_server(
                    process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
                )

            process.wait()

            _, err = capfd.readouterr()
            assert "No module named" in err
        finally:
            if process.poll() is None:
                process.terminate()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Crashes in subprocesses crash test runs on Windows")
def test_crash_during_load():
    port = find_free_port()
    python_file = file_relative_path(__file__, "crashy_grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(
        subprocess_args,
        stdout=subprocess.PIPE,
    )
    try:

        with pytest.raises(
            Exception,
            match=re.escape(
                'gRPC server exited with return code 123 while starting up with the command: "dagster api grpc --port'
            ),
        ):
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
    finally:
        if process.poll() is None:
            process.terminate()


def test_load_timeout():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_that_times_out.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(subprocess_args, stdout=subprocess.PIPE)

    timeout_exception = None

    try:
        try:
            wait_for_grpc_server(
                process,
                DagsterGrpcClient(port=port, host="localhost"),
                subprocess_args,
                timeout=0.01,
            )
            assert False, "server should have timed out"
        except Exception as e:
            timeout_exception = e

    finally:
        process.terminate()

    assert "Timed out waiting for gRPC server to start" in str(timeout_exception)
    assert "Most recent connection error: " in str(timeout_exception)
    assert "StatusCode.UNAVAILABLE" in str(timeout_exception)


def test_lazy_load_with_error():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--lazy-load-user-code",
    ]

    process = subprocess.Popen(subprocess_args, stdout=subprocess.PIPE)

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        list_repositories_response = deserialize_json_to_dagster_namedtuple(
            DagsterGrpcClient(port=port).list_repositories()
        )
        assert isinstance(list_repositories_response, SerializableErrorInfo)
        assert "No module named" in list_repositories_response.message
    finally:
        process.terminate()


def test_lazy_load_via_env_var():
    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        port = find_free_port()
        python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

        subprocess_args = [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
        ]

        process = subprocess.Popen(
            subprocess_args,
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            list_repositories_response = deserialize_json_to_dagster_namedtuple(
                DagsterGrpcClient(port=port).list_repositories()
            )
            assert isinstance(list_repositories_response, SerializableErrorInfo)
            assert "No module named" in list_repositories_response.message
        finally:
            process.terminate()


def test_streaming():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(
        subprocess_args,
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        api_client = DagsterGrpcClient(port=port)
        results = [result for result in api_client.streaming_ping(sequence_length=10, echo="foo")]
        assert len(results) == 10
        for sequence_number, result in enumerate(results):
            assert result["sequence_number"] == sequence_number
            assert result["echo"] == "foo"
    finally:
        process.terminate()


def test_sensor_timeout():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(
        subprocess_args,
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        client = DagsterGrpcClient(port=port)

        with instance_for_test() as instance:
            repo_origin = ExternalRepositoryOrigin(
                repository_location_origin=GrpcServerRepositoryLocationOrigin(
                    port=port, host="localhost"
                ),
                repository_name="bar_repo",
            )
            with pytest.raises(Exception, match="Deadline Exceeded"):
                client.external_sensor_execution(
                    sensor_execution_args=SensorExecutionArgs(
                        repository_origin=repo_origin,
                        instance_ref=instance.get_ref(),
                        sensor_name="slow_sensor",
                        last_completion_time=None,
                        last_run_key=None,
                        cursor=None,
                    ),
                    timeout=2,
                )

            # Call succeeds without the timeout
            client.external_sensor_execution(
                sensor_execution_args=SensorExecutionArgs(
                    repository_origin=repo_origin,
                    instance_ref=instance.get_ref(),
                    sensor_name="slow_sensor",
                    last_completion_time=None,
                    last_run_key=None,
                    cursor=None,
                ),
            )
    finally:
        process.terminate()
