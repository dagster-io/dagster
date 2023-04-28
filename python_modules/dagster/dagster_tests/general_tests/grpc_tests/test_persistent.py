import json
import os
import re
import subprocess
import sys
import uuid

import pytest
from dagster import _seven
from dagster._api.list_repositories import sync_list_repositories_grpc
from dagster._core.errors import DagsterUserCodeUnreachableError
from dagster._core.host_representation.origin import (
    ExternalJobOrigin,
    ExternalRepositoryOrigin,
    GrpcServerCodeLocationOrigin,
    RegisteredCodeLocationOrigin,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import (
    create_run_for_test,
    environ,
    instance_for_test,
    new_cwd,
    poll_for_finished_run,
)
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.server import (
    ExecuteExternalJobArgs,
    open_server_process,
    wait_for_grpc_server,
)
from dagster._grpc.types import ListRepositoriesResponse, SensorExecutionArgs, StartRunResult
from dagster._serdes import serialize_value
from dagster._serdes.serdes import deserialize_value
from dagster._seven import get_system_temp_directory
from dagster._utils import file_relative_path, find_free_port
from dagster._utils.error import SerializableErrorInfo
from dagster.version import __version__ as dagster_version


def _get_ipc_output_file():
    return os.path.join(get_system_temp_directory(), f"grpc-server-startup-{uuid.uuid4().hex}")


def test_load_grpc_server(capfd):
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

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")

        wait_for_grpc_server(process, client, subprocess_args)
        assert client.ping("foobar") == "foobar"

        list_repositories_response = sync_list_repositories_grpc(client)
        assert list_repositories_response.entry_point == ["dagster"]
        assert list_repositories_response.executable_path == sys.executable

        subprocess.check_call(["dagster", "api", "grpc-health-check", "--port", str(port)])

        ssl_result = subprocess.run(
            ["dagster", "api", "grpc-health-check", "--port", str(port), "--use-ssl"]
        )
        assert ssl_result.returncode == 1

    finally:
        process.terminate()
        process.wait()

    out, _err = capfd.readouterr()

    assert f"Started Dagster code server for file {python_file} on port {port} in process" in out


def test_grpc_connection_error():
    port = find_free_port()
    client = DagsterGrpcClient(port=port, host="localhost")
    with pytest.raises(
        DagsterUserCodeUnreachableError,
        match="Could not reach user code server. gRPC Error code: UNAVAILABLE",
    ):
        client.ping("foobar")


def test_python_environment_args():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=python_file
    )

    with instance_for_test() as instance:
        process = None
        try:
            process = open_server_process(
                instance.get_ref(), port, socket=None, loadable_target_origin=loadable_target_origin
            )
            assert process.args[:5] == [sys.executable, "-m", "dagster", "api", "grpc"]
        finally:
            if process:
                process.terminate()
                process.wait()


def test_empty_executable_args():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")
    loadable_target_origin = LoadableTargetOrigin(executable_path="", python_file=python_file)
    # with an empty executable_path, the args change
    process = None
    with instance_for_test() as instance:
        try:
            process = open_server_process(
                instance.get_ref(), port, socket=None, loadable_target_origin=loadable_target_origin
            )
            assert process.args[:5] == [sys.executable, "-m", "dagster", "api", "grpc"]

            client = DagsterGrpcClient(port=port, host="localhost")
            list_repositories_response = sync_list_repositories_grpc(client)
            assert list_repositories_response.entry_point == ["dagster"]
            assert list_repositories_response.executable_path == sys.executable
        finally:
            if process:
                process.terminate()
                process.wait()


def test_load_grpc_server_python_env():
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
        "--use-python-environment-entry-point",
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")

        wait_for_grpc_server(process, client, subprocess_args)

        list_repositories_response = sync_list_repositories_grpc(client)
        assert list_repositories_response.entry_point == [sys.executable, "-m", "dagster"]
        assert list_repositories_response.executable_path == sys.executable

    finally:
        process.terminate()
        process.wait()


def test_load_via_auto_env_var_prefix():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = ["dagster", "api", "grpc"]

    container_context = {
        "k8s": {
            "image_pull_policy": "Never",
            "image_pull_secrets": [{"name": "your_secret"}],
        }
    }

    container_image = "myregistry/my_image:latest"

    with environ(
        {
            "DAGSTER_CLI_API_GRPC_HOST": "localhost",
            "DAGSTER_CLI_API_GRPC_PORT": str(port),
            "DAGSTER_CLI_API_GRPC_PYTHON_FILE": python_file,
            "DAGSTER_CLI_API_GRPC_CONTAINER_IMAGE": container_image,
            "DAGSTER_CLI_API_GRPC_CONTAINER_CONTEXT": json.dumps(container_context),
        }
    ):
        process = subprocess.Popen(
            subprocess_args,
            stdout=subprocess.PIPE,
        )

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            client = DagsterGrpcClient(port=port)
            assert client.ping("foobar") == "foobar"

            list_repositories_response = sync_list_repositories_grpc(client)
            assert list_repositories_response.container_image == container_image
            assert list_repositories_response.container_context == container_context

        finally:
            process.terminate()
            process.wait()


def test_load_via_env_var():
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = ["dagster", "api", "grpc"]

    container_context = {
        "k8s": {
            "image_pull_policy": "Never",
            "image_pull_secrets": [{"name": "your_secret"}],
        }
    }

    container_image = "myregistry/my_image:latest"

    with environ(
        {
            "DAGSTER_PYTHON_FILE": python_file,
            "DAGSTER_GRPC_HOST": "localhost",
            "DAGSTER_GRPC_PORT": str(port),
            "DAGSTER_CONTAINER_IMAGE": container_image,
            "DAGSTER_CONTAINER_CONTEXT": json.dumps(container_context),
        }
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
            process.wait()


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
            match=(
                'gRPC server exited with return code 2 while starting up with the command: "dagster'
                " api grpc --port"
            ),
        ):
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
    finally:
        process.terminate()
        process.wait()

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
        assert "Dagster recognizes standard cron expressions" in err
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


def test_load_with_non_existant_file(capfd):
    port = find_free_port()
    # File that will fail if working directory isn't set to default
    python_file = file_relative_path(__file__, "made_up_file_does_not_exist.py")

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_output(
            ["dagster", "api", "grpc", "--port", str(port), "--python-file", python_file],
        )

    _, err = capfd.readouterr()

    if _seven.IS_WINDOWS:
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
            process.wait()

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
                process.wait()


@pytest.mark.skipif(_seven.IS_WINDOWS, reason="Crashes in subprocesses crash test runs on Windows")
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
                "gRPC server exited with return code 123 while starting up with the command:"
                ' "dagster api grpc --port'
            ),
        ):
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


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
        process.wait()

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
        list_repositories_response = deserialize_value(
            DagsterGrpcClient(port=port).list_repositories(), SerializableErrorInfo
        )
        assert "Dagster recognizes standard cron expressions" in list_repositories_response.message
    finally:
        process.terminate()
        process.wait()


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
            list_repositories_response = deserialize_value(
                DagsterGrpcClient(port=port).list_repositories(), SerializableErrorInfo
            )
            assert (
                "Dagster recognizes standard cron expressions" in list_repositories_response.message
            )
        finally:
            process.terminate()
            process.wait()


def test_load_with_missing_env_var():
    port = find_free_port()
    client = DagsterGrpcClient(port=port)
    python_file = file_relative_path(__file__, "grpc_repo_with_env_vars.py")

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
        wait_for_grpc_server(process, client, subprocess_args)
        list_repositories_response = deserialize_value(
            client.list_repositories(), SerializableErrorInfo
        )
        assert "Missing env var" in list_repositories_response.message
    finally:
        client.shutdown_server()
        process.communicate(timeout=30)


def test_load_with_secrets_loader_instance_ref():
    # Now with secrets manager and correct args
    port = find_free_port()
    client = DagsterGrpcClient(port=port)

    python_file = file_relative_path(__file__, "grpc_repo_with_env_vars.py")
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

    with environ({"FOO": None, "FOO_INSIDE_OP": None}):
        with instance_for_test(
            set_dagster_home=False,
        ) as instance:
            process = subprocess.Popen(
                subprocess_args
                + [
                    "--inject-env-vars-from-instance",
                    "--instance-ref",
                    serialize_value(instance.get_ref()),
                ],
                cwd=os.path.dirname(__file__),
            )
            try:
                wait_for_grpc_server(process, client, subprocess_args)

                deserialize_value(client.list_repositories(), ListRepositoriesResponse)

                # Launch a run and verify that it finishes

                run = create_run_for_test(instance, job_name="needs_env_var_job")
                run_id = run.run_id

                job_origin = ExternalJobOrigin(
                    job_name="needs_env_var_job",
                    external_repository_origin=ExternalRepositoryOrigin(
                        repository_name="needs_env_var_repo",
                        code_location_origin=RegisteredCodeLocationOrigin("not_used"),
                    ),
                )

                res = deserialize_value(
                    client.start_run(
                        ExecuteExternalJobArgs(
                            job_origin=job_origin,
                            run_id=run.run_id,
                            instance_ref=instance.get_ref(),
                        )
                    ),
                    StartRunResult,
                )

                assert res.success
                finished_run = poll_for_finished_run(instance, run_id)

                assert finished_run
                assert finished_run.run_id == run_id
                assert finished_run.status == DagsterRunStatus.SUCCESS

            finally:
                client.shutdown_server()
                process.communicate(timeout=30)


def test_load_with_secrets_loader_no_instance_ref():
    port = find_free_port()
    client = DagsterGrpcClient(port=port)
    python_file = file_relative_path(__file__, "grpc_repo_with_env_vars.py")

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

    with environ({"FOO": None}):
        with instance_for_test(
            set_dagster_home=True,
        ):
            process = subprocess.Popen(
                subprocess_args + ["--inject-env-vars-from-instance"],
                cwd=os.path.dirname(__file__),
            )

            client = DagsterGrpcClient(port=port, host="localhost")

            try:
                wait_for_grpc_server(process, client, subprocess_args)
                deserialize_value(
                    DagsterGrpcClient(port=port).list_repositories(), ListRepositoriesResponse
                )

            finally:
                client.shutdown_server()
                process.communicate(timeout=30)


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
        process.wait()


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
                code_location_origin=GrpcServerCodeLocationOrigin(port=port, host="localhost"),
                repository_name="bar_repo",
            )
            with pytest.raises(DagsterUserCodeUnreachableError) as exc_info:
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

            assert "Deadline Exceeded" in str(exc_info.getrepr())

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
        process.wait()


def test_load_with_container_context(capfd):
    port = find_free_port()
    python_file = file_relative_path(__file__, "grpc_repo.py")

    container_context = {
        "k8s": {
            "image_pull_policy": "Never",
            "image_pull_secrets": [{"name": "your_secret"}],
        }
    }

    subprocess_args = [
        "dagster",
        "api",
        "grpc",
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--container-context",
        json.dumps(container_context),
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")

        wait_for_grpc_server(process, client, subprocess_args)
        assert client.ping("foobar") == "foobar"

        list_repositories_response = sync_list_repositories_grpc(client)
        assert list_repositories_response.entry_point == ["dagster"]
        assert list_repositories_response.executable_path == sys.executable
        assert list_repositories_response.container_context == container_context
        assert list_repositories_response.dagster_library_versions == {"dagster": dagster_version}

    finally:
        process.terminate()
        process.wait()

    out, _err = capfd.readouterr()

    assert f"Started Dagster code server for file {python_file} on port {port} in process" in out
