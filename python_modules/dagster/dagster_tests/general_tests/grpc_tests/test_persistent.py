import os
import re
import subprocess
import uuid

import pytest
from dagster import seven
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.core.host_representation.origin import (
    ExternalRepositoryOrigin,
    GrpcServerRepositoryLocationOrigin,
)
from dagster.core.test_utils import environ, instance_for_test, new_cwd
from dagster.grpc.client import DagsterGrpcClient
from dagster.grpc.server import wait_for_grpc_server
from dagster.grpc.types import SensorExecutionArgs
from dagster.serdes.ipc import DagsterIPCProtocolError
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

    ipc_output_file = _get_ipc_output_file()
    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process, ipc_output_file)
        assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
    finally:
        process.terminate()


def test_load_via_env_var():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    with environ(
        {"DAGSTER_CLI_API_GRPC_HOST": "localhost", "DAGSTER_CLI_API_GRPC_PORT": str(port)}
    ):
        ipc_output_file = _get_ipc_output_file()
        process = subprocess.Popen(
            [
                "dagster",
                "api",
                "grpc",
                "--python-file",
                python_file,
                "--ipc-output-file",
                ipc_output_file,
            ],
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(process, ipc_output_file)
            assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
        finally:
            process.terminate()


def test_load_with_invalid_param(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    ipc_output_file = _get_ipc_output_file()
    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
            "--foo-param",
            "bar_value",
        ],
        stdout=subprocess.PIPE,
    )

    try:
        with pytest.raises(DagsterIPCProtocolError):
            wait_for_grpc_server(process, ipc_output_file)
    finally:
        process.terminate()

    _, err = capfd.readouterr()
    assert "no such optio" in err


def test_load_with_error(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    ipc_output_file = _get_ipc_output_file()

    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )

    try:
        with pytest.raises(DagsterUserCodeProcessError):
            wait_for_grpc_server(process, ipc_output_file)

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

    with new_cwd(os.path.dirname(__file__)):

        ipc_output_file = _get_ipc_output_file()

        process = subprocess.Popen(
            [
                "dagster",
                "api",
                "grpc",
                "--port",
                str(port),
                "--python-file",
                python_file,
                "--ipc-output-file",
                ipc_output_file,
            ],
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(process, ipc_output_file)
            assert DagsterGrpcClient(port=port).ping("foobar") == "foobar"
        finally:
            process.terminate()

        # indicating the working directory is empty fails

        ipc_output_file = _get_ipc_output_file()

        process = subprocess.Popen(
            [
                "dagster",
                "api",
                "grpc",
                "--port",
                str(port),
                "--python-file",
                python_file,
                "--empty-working-directory",
                "--ipc-output-file",
                ipc_output_file,
            ],
            stdout=subprocess.PIPE,
        )
        try:
            with pytest.raises(DagsterUserCodeProcessError):
                wait_for_grpc_server(process, ipc_output_file)

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

    ipc_output_file = _get_ipc_output_file()

    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )
    try:

        with pytest.raises(
            Exception,
            match=re.escape("Process exited with return code 123 while waiting for events"),
        ):
            wait_for_grpc_server(process, ipc_output_file)

    finally:
        if process.poll() is None:
            process.terminate()


def test_lazy_load_with_error():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

    ipc_output_file = _get_ipc_output_file()

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
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process, ipc_output_file)
        list_repositories_response = DagsterGrpcClient(port=port).list_repositories()
        assert isinstance(list_repositories_response, SerializableErrorInfo)
        assert "No module named" in list_repositories_response.message
    finally:
        process.terminate()


def test_lazy_load_via_env_var():
    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        port = find_free_port()
        python_file = file_relative_path(__file__, "grpc_repo_with_error.py")

        ipc_output_file = _get_ipc_output_file()

        process = subprocess.Popen(
            [
                "dagster",
                "api",
                "grpc",
                "--port",
                str(port),
                "--python-file",
                python_file,
                "--ipc-output-file",
                ipc_output_file,
            ],
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(process, ipc_output_file)
            list_repositories_response = DagsterGrpcClient(port=port).list_repositories()
            assert isinstance(list_repositories_response, SerializableErrorInfo)
            assert "No module named" in list_repositories_response.message
        finally:
            process.terminate()


def test_streaming():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    ipc_output_file = _get_ipc_output_file()

    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process, ipc_output_file)
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

    ipc_output_file = _get_ipc_output_file()
    process = subprocess.Popen(
        [
            "dagster",
            "api",
            "grpc",
            "--port",
            str(port),
            "--python-file",
            python_file,
            "--ipc-output-file",
            ipc_output_file,
        ],
        stdout=subprocess.PIPE,
    )

    try:
        wait_for_grpc_server(process, ipc_output_file)
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
                ),
            )
    finally:
        process.terminate()
