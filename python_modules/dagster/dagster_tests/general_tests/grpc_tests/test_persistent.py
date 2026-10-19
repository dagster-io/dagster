import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import dagster as dg
import psutil
import pytest
from dagster._api.list_repositories import sync_list_repositories_grpc
from dagster._core.errors import DagsterUserCodeProcessError, DagsterUserCodeUnreachableError
from dagster._core.remote_origin import (
    GrpcServerCodeLocationOrigin,
    RegisteredCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster._core.remote_representation.external_data import SensorExecutionErrorSnap
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.test_utils import create_run_for_test, environ, new_cwd, poll_for_finished_run
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._grpc import proxy_server
from dagster._grpc.client import DagsterGrpcClient
from dagster._grpc.constants import GrpcServerCommand
from dagster._grpc.proxy_server import (
    MAX_SUBPROCESS_RESTART_BACKOFF,
    SUBPROCESS_WATCHDOG_INTERVAL,
    DagsterProxyApiServicer,
    next_subprocess_restart_backoff,
)
from dagster._grpc.server import ExecuteExternalJobArgs, open_server_process, wait_for_grpc_server
from dagster._grpc.types import (
    JobSubsetSnapshotArgs,
    ListRepositoriesResponse,
    SensorExecutionArgs,
    StartRunResult,
)
from dagster._utils import find_free_port, safe_tempfile_path_unmanaged
from dagster._utils.error import SerializableErrorInfo
from dagster.version import __version__ as dagster_version
from dagster_shared import seven
from dagster_shared.version import __version__ as dagster_shared_version


def entrypoints():
    return [
        ["dagster", "api", "grpc"],
        ["dagster", "code-server", "start"],
    ]


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_grpc_server(entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = entrypoint + [
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")

        wait_for_grpc_server(process, client, subprocess_args)
        assert client.ping("foobar") == {
            "echo": "foobar",
            "serialized_server_utilization_metrics": "",
        }

        list_repositories_response = sync_list_repositories_grpc(client)
        assert list_repositories_response.entry_point == ["dagster"]
        assert list_repositories_response.executable_path == sys.executable

        subprocess.check_call(["dagster", "api", "grpc-health-check", "--port", str(port)])

        ssl_result = subprocess.run(
            ["dagster", "api", "grpc-health-check", "--port", str(port), "--use-ssl"], check=False
        )
        assert ssl_result.returncode == 1

    finally:
        process.terminate()
        process.communicate(timeout=30)


def test_grpc_connection_error():
    port = find_free_port()
    client = DagsterGrpcClient(port=port, host="localhost")
    with pytest.raises(
        DagsterUserCodeUnreachableError,
        match=r"Could not reach user code server. gRPC Error code: UNAVAILABLE",
    ):
        client.ping("foobar")


def test_python_environment_args():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=python_file
    )

    with dg.instance_for_test() as instance:
        process = None
        try:
            process = open_server_process(
                server_command=GrpcServerCommand.API_GRPC,
                instance_ref=instance.get_ref(),
                port=port,
                socket=None,
                loadable_target_origin=loadable_target_origin,
            )
            assert process.args[:5] == [sys.executable, "-m", "dagster", "api", "grpc"]
        finally:
            if process:
                process.terminate()
                process.wait()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Windows requires ports")
def test_env_var_port_collision():
    port = find_free_port()
    socket = safe_tempfile_path_unmanaged()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable, python_file=python_file
    )

    with dg.instance_for_test() as instance:
        process = None
        try:
            # env var that would cause a collision with port if we are not careful
            with environ({"DAGSTER_GRPC_SOCKET": str(socket)}):
                process = open_server_process(
                    instance_ref=instance.get_ref(),
                    port=port,
                    server_command=GrpcServerCommand.API_GRPC,
                    socket=None,
                    loadable_target_origin=loadable_target_origin,
                )
                client = DagsterGrpcClient(port=port, host="localhost")
                wait_for_grpc_server(process, client, [])
        finally:
            if process:
                process.terminate()
                process.wait()

        try:
            # env var that would cause a collision with socket if we are not careful
            with environ({"DAGSTER_GRPC_PORT": str(port)}):
                process = open_server_process(
                    instance_ref=instance.get_ref(),
                    server_command=GrpcServerCommand.API_GRPC,
                    port=None,
                    socket=socket,
                    loadable_target_origin=loadable_target_origin,
                )
                client = DagsterGrpcClient(socket=socket, host="localhost")
                wait_for_grpc_server(process, client, [])
        finally:
            if process:
                process.terminate()
                process.wait()


def test_empty_executable_args():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")
    loadable_target_origin = LoadableTargetOrigin(executable_path="", python_file=python_file)
    # with an empty executable_path, the args change
    process = None
    with dg.instance_for_test() as instance:
        try:
            process = open_server_process(
                instance_ref=instance.get_ref(),
                port=port,
                server_command=GrpcServerCommand.API_GRPC,
                socket=None,
                loadable_target_origin=loadable_target_origin,
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


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_grpc_server_python_env(entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = entrypoint + [
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
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

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
        process = subprocess.Popen(subprocess_args)

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            client = DagsterGrpcClient(port=port)
            assert client.ping("foobar") == {
                "echo": "foobar",
                "serialized_server_utilization_metrics": "",
            }

            list_repositories_response = sync_list_repositories_grpc(client)
            assert list_repositories_response.container_image == container_image
            assert list_repositories_response.container_context == container_context

        finally:
            process.terminate()
            process.wait()


def test_load_via_env_var():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

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
        process = subprocess.Popen(subprocess_args)

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            assert DagsterGrpcClient(port=port).ping("foobar") == {
                "echo": "foobar",
                "serialized_server_utilization_metrics": "",
            }
        finally:
            process.terminate()
            process.wait()


def test_load_code_server_via_env_var():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = ["dagster", "code-server", "start"]

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
            "DAGSTER_CODE_SERVER_HOST": "localhost",
            "DAGSTER_CODE_SERVER_PORT": str(port),
            "DAGSTER_CONTAINER_IMAGE": container_image,
            "DAGSTER_CONTAINER_CONTEXT": json.dumps(container_context),
        }
    ):
        process = subprocess.Popen(subprocess_args)

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            assert DagsterGrpcClient(port=port).ping("foobar") == {
                "echo": "foobar",
                "serialized_server_utilization_metrics": "",
            }
        finally:
            process.terminate()
            process.wait()


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_with_invalid_param(capfd, entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = entrypoint + [
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--foo-param",
        "bar_value",
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        with pytest.raises(
            Exception,
            match="exited with return code 2 while starting up with the command",
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
    python_file = dg.file_relative_path(__file__, "grpc_repo_with_error.py")

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
        with pytest.raises(Exception):
            wait_for_grpc_server(process, client, subprocess_args)

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
    python_file = dg.file_relative_path(__file__, "made_up_file_does_not_exist.py")

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
    python_file = dg.file_relative_path(__file__, "grpc_repo_with_local_import.py")

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
        process = subprocess.Popen(subprocess_args)

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            assert DagsterGrpcClient(port=port).ping("foobar") == {
                "echo": "foobar",
                "serialized_server_utilization_metrics": "",
            }
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

        process = subprocess.Popen(subprocess_args)
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


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Crashes in subprocesses crash test runs on Windows")
def test_crash_during_load():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "crashy_grpc_repo.py")

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
    python_file = dg.file_relative_path(__file__, "grpc_repo_that_times_out.py")

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

    timeout_exception = None

    try:
        try:
            wait_for_grpc_server(
                process,
                DagsterGrpcClient(port=port, host="localhost"),
                subprocess_args,
                timeout=0.01,  # ty: ignore[invalid-argument-type]
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


def test_server_heartbeat_timeout_code_server_cli() -> None:
    """Test that without a heartbeat from the calling process, the server will eventually time out."""
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "slow_grpc_repo.py")

    subprocess_args = [
        "dagster",
        "code-server",
        "start",
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--heartbeat",
        "--heartbeat-timeout",
        "5",
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")
        wait_for_grpc_server(
            process,
            DagsterGrpcClient(port=port, host="localhost"),
            subprocess_args,
        )
        # Send out an initial heartbeat, ensure server is alive to begin with.
        client.ping("foobar")
        client.shutdown_server()
        assert process.poll() is None
        time.sleep(6)
        assert process.poll() == 0

    finally:
        process.terminate()
        process.wait()


def _code_server_subprocesses(code_server: subprocess.Popen) -> list[psutil.Process]:
    return [
        child
        for child in psutil.Process(code_server.pid).children()
        if "grpc" in " ".join(child.cmdline())
    ]


def _start_code_server(
    python_file: str,
) -> tuple[subprocess.Popen, DagsterGrpcClient, list[str]]:
    port = find_free_port()
    args = ["dagster", "code-server", "start", "--port", str(port), "--python-file", python_file]
    return subprocess.Popen(args), DagsterGrpcClient(port=port, host="localhost"), args


def test_subprocess_restart_backoff_schedule() -> None:
    # A subprocess that keeps crashing right after it starts backs off, doubling up to the cap
    backoff = 0.0
    schedule = []
    for _ in range(9):
        backoff = next_subprocess_restart_backoff(backoff, uptime=1)
        schedule.append(backoff)
    assert schedule == [5, 10, 20, 40, 80, 160, 300, 300, 300]

    # ...stays at the cap even though each wait is as long as the cap...
    assert (
        next_subprocess_restart_backoff(
            MAX_SUBPROCESS_RESTART_BACKOFF, uptime=MAX_SUBPROCESS_RESTART_BACKOFF - 1
        )
        == MAX_SUBPROCESS_RESTART_BACKOFF
    )

    # ...and one that stayed up long enough is restarted right away
    assert (
        next_subprocess_restart_backoff(
            MAX_SUBPROCESS_RESTART_BACKOFF, uptime=MAX_SUBPROCESS_RESTART_BACKOFF
        )
        == 0
    )
    assert next_subprocess_restart_backoff(0, uptime=1) == SUBPROCESS_WATCHDOG_INTERVAL


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Kills a subprocess by pid")
def test_code_server_restarts_exited_subprocess() -> None:
    process, client, args = _start_code_server(dg.file_relative_path(__file__, "grpc_repo.py"))
    try:
        wait_for_grpc_server(process, client, args)
        original_server_id = client.get_server_id()
        [subprocess_before] = _code_server_subprocesses(process)

        subprocess_before.kill()
        subprocess_before.wait(timeout=10)

        start = time.time()
        while True:
            try:
                if client.get_server_id() != original_server_id:
                    break
            except DagsterUserCodeUnreachableError:
                pass
            assert time.time() - start < 60, "code server did not restart its subprocess"
            time.sleep(1)

        assert process.poll() is None
        assert client.ping("foobar")["echo"] == "foobar"
        assert isinstance(sync_list_repositories_grpc(client), ListRepositoriesResponse)
        assert len(_code_server_subprocesses(process)) == 1
    finally:
        process.terminate()
        process.wait()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Crashes in subprocesses crash test runs on Windows")
def test_code_server_does_not_restart_subprocess_after_load_error() -> None:
    process, client, _ = _start_code_server(dg.file_relative_path(__file__, "crashy_grpc_repo.py"))
    try:
        # Ping fails without a subprocess, so wait on the proxy's own health check.
        start = time.time()
        while client.health_check_query() != "SERVING":
            assert time.time() - start < 60, "code server did not start"
            time.sleep(1)

        # Several watchdog intervals: a failed load must not be retried in a loop.
        for _ in range(12):
            assert _code_server_subprocesses(process) == []
            time.sleep(1)

        assert process.poll() is None
        with pytest.raises(DagsterUserCodeProcessError):
            sync_list_repositories_grpc(client)
    finally:
        process.terminate()
        process.wait()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Kills a subprocess by pid")
def test_code_server_reload_after_subprocess_exit_starts_one_subprocess() -> None:
    process, client, args = _start_code_server(dg.file_relative_path(__file__, "grpc_repo.py"))
    try:
        wait_for_grpc_server(process, client, args)
        [subprocess_before] = _code_server_subprocesses(process)

        # The watchdog may also try to replace it; the in-process tests below fix that order.
        subprocess_before.kill()
        subprocess_before.wait(timeout=10)
        client.reload_code(timeout=60)

        # Long enough for the watchdog to have run, and for any replaced subprocess to exit.
        time.sleep(15)
        assert len(_code_server_subprocesses(process)) == 1
        assert client.ping("foobar")["echo"] == "foobar"
    finally:
        process.terminate()
        process.wait()


@contextmanager
def _in_process_proxy_servicer(monkeypatch) -> Iterator[DagsterProxyApiServicer]:
    # Keep the watchdog out of the way: these tests run its restart step themselves.
    monkeypatch.setattr(proxy_server, "SUBPROCESS_WATCHDOG_INTERVAL", 3600)
    servicer = DagsterProxyApiServicer(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=dg.file_relative_path(__file__, "grpc_repo.py"),
        ),
        fixed_server_id=None,
        container_image=None,
        container_context=None,
        inject_env_vars_from_instance=False,
        location_name=None,
        log_level="INFO",
        startup_timeout=60,
        server_termination_event=threading.Event(),
        instance_ref=None,
        logger=logging.getLogger("dagster.code_server"),
        server_heartbeat=False,
        server_heartbeat_timeout=30,
        heartbeat_ttl=30,
        defs_state_info=None,
    )
    try:
        yield servicer
    finally:
        servicer.cleanup()


def _active_subprocess(servicer: DagsterProxyApiServicer) -> subprocess.Popen:
    registry = servicer._grpc_server_registry  # noqa: SLF001
    entry = registry._active_entries[servicer._origin.get_id()]  # noqa: SLF001
    return entry.process.server_process


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Kills a subprocess by pid")
def test_reload_when_subprocess_exits_while_replacement_starts(monkeypatch) -> None:
    with _in_process_proxy_servicer(monkeypatch) as servicer:
        old_subprocess = _active_subprocess(servicer)
        old_heartbeat_thread = servicer._client_heartbeat_thread  # noqa: SLF001
        assert old_heartbeat_thread

        reload_location = servicer._reload_location  # noqa: SLF001

        def exit_then_reload_location():
            old_subprocess.kill()
            old_subprocess.wait(timeout=10)
            reload_location()

        monkeypatch.setattr(servicer, "_reload_location", exit_then_reload_location)
        servicer.ReloadCode(None, None)

        assert _active_subprocess(servicer) is not old_subprocess
        client = servicer._client  # noqa: SLF001
        assert client
        assert client.ping("foobar")["echo"] == "foobar"
        assert not old_heartbeat_thread.is_alive()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Kills a subprocess by pid")
def test_watchdog_does_not_replace_subprocess_that_reload_already_replaced(monkeypatch) -> None:
    with _in_process_proxy_servicer(monkeypatch) as servicer:
        old_subprocess = _active_subprocess(servicer)
        old_subprocess.kill()
        old_subprocess.wait(timeout=10)

        # The watchdog has seen the exit, but a ReloadCode replaces the subprocess first...
        registry = servicer._grpc_server_registry  # noqa: SLF001
        assert registry.get_active_process_exit_code(servicer._origin) is not None  # noqa: SLF001
        servicer.ReloadCode(None, None)
        new_subprocess = _active_subprocess(servicer)

        # ...so when the watchdog acts on what it saw, there is nothing left to replace.
        assert servicer._restart_subprocess(only_if_exited=True) is False  # noqa: SLF001
        assert _active_subprocess(servicer) is new_subprocess
        assert new_subprocess.poll() is None


def test_load_timeout_code_server_cli() -> None:
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo_that_times_out.py")

    subprocess_args = [
        "dagster",
        "code-server",
        "start",
        "--port",
        str(port),
        "--python-file",
        python_file,
        "--startup-timeout",
        "1",
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        with pytest.raises(
            Exception,
        ) as exc_info:
            wait_for_grpc_server(
                process,
                DagsterGrpcClient(port=port, host="localhost"),
                subprocess_args,
            )
        assert "Timed out waiting for gRPC server to start" in str(exc_info.value)
        assert "Most recent connection error: " in str(exc_info.value)
        assert "StatusCode.UNKNOWN" in str(exc_info.value)

    finally:
        process.terminate()
        process.wait()


def test_lazy_load_with_error():
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo_with_error.py")

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

    process = subprocess.Popen(subprocess_args)

    try:
        client = DagsterGrpcClient(port=port, host="localhost")
        wait_for_grpc_server(process, client, subprocess_args)
        list_repositories_response = dg.deserialize_value(
            DagsterGrpcClient(port=port).list_repositories(), SerializableErrorInfo
        )
        assert "Dagster recognizes standard cron expressions" in list_repositories_response.message

        repo_origin = RemoteRepositoryOrigin(
            code_location_origin=GrpcServerCodeLocationOrigin(port=port, host="localhost"),
            repository_name="bar_repo",
        )

        sensor_execution_response = dg.deserialize_value(
            client.external_sensor_execution(
                sensor_execution_args=SensorExecutionArgs(
                    repository_origin=repo_origin,
                    instance_ref=None,
                    sensor_name="nonexistant_sensor",
                    last_tick_completion_time=None,
                    last_run_key=None,
                    cursor=None,
                    last_sensor_start_time=None,
                )
            ),
            SensorExecutionErrorSnap,
        )
        assert "Dagster recognizes standard cron expressions" in str(
            sensor_execution_response.error
        )

    finally:
        process.terminate()
        process.wait()


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_lazy_load_via_env_var(entrypoint):
    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        port = find_free_port()
        python_file = dg.file_relative_path(__file__, "grpc_repo_with_error.py")

        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            python_file,
        ]

        process = subprocess.Popen(subprocess_args)

        try:
            wait_for_grpc_server(
                process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
            )
            list_repositories_response = dg.deserialize_value(
                DagsterGrpcClient(port=port).list_repositories(), SerializableErrorInfo
            )
            assert (
                "Dagster recognizes standard cron expressions" in list_repositories_response.message
            )
        finally:
            process.terminate()
            process.wait()


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_with_missing_env_var(entrypoint):
    port = find_free_port()
    client = DagsterGrpcClient(port=port)
    python_file = dg.file_relative_path(__file__, "grpc_repo_with_env_vars.py")

    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            python_file,
        ]

        process = subprocess.Popen(subprocess_args)
        try:
            wait_for_grpc_server(process, client, subprocess_args)
            list_repositories_response = dg.deserialize_value(
                client.list_repositories(), SerializableErrorInfo
            )
            assert "Missing env var" in str(list_repositories_response)
        finally:
            client.shutdown_server()
            process.communicate(timeout=30)


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_with_secrets_loader_instance_ref(entrypoint):
    # Now with secrets manager and correct args
    port = find_free_port()
    client = DagsterGrpcClient(port=port)

    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        python_file = dg.file_relative_path(__file__, "grpc_repo_with_env_vars.py")
        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            python_file,
        ]

        with environ({"FOO": None, "FOO_INSIDE_OP": None}):  # ty: ignore[invalid-argument-type]
            with dg.instance_for_test(
                set_dagster_home=False,
            ) as instance:
                process = subprocess.Popen(
                    subprocess_args
                    + [
                        "--inject-env-vars-from-instance",
                        "--instance-ref",
                        dg.serialize_value(instance.get_ref()),
                    ],
                    cwd=os.path.dirname(__file__),
                )
                try:
                    wait_for_grpc_server(process, client, subprocess_args)

                    dg.deserialize_value(client.list_repositories(), ListRepositoriesResponse)

                    # Launch a run and verify that it finishes

                    run = create_run_for_test(instance, job_name="needs_env_var_job")
                    run_id = run.run_id

                    job_origin = RemoteJobOrigin(
                        job_name="needs_env_var_job",
                        repository_origin=RemoteRepositoryOrigin(
                            repository_name="needs_env_var_repo",
                            code_location_origin=RegisteredCodeLocationOrigin("not_used"),
                        ),
                    )

                    res = dg.deserialize_value(
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


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_with_secrets_loader_no_instance_ref(entrypoint):
    port = find_free_port()
    client = DagsterGrpcClient(port=port)
    python_file = dg.file_relative_path(__file__, "grpc_repo_with_env_vars.py")

    with environ({"DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1"}):
        subprocess_args = entrypoint + [
            "--port",
            str(port),
            "--python-file",
            python_file,
        ]

        with environ({"FOO": None}):  # ty: ignore[invalid-argument-type]
            with dg.instance_for_test(
                set_dagster_home=True,
            ):
                process = subprocess.Popen(
                    subprocess_args + ["--inject-env-vars-from-instance"],
                    cwd=os.path.dirname(__file__),
                )

                client = DagsterGrpcClient(port=port, host="localhost")

                try:
                    wait_for_grpc_server(process, client, subprocess_args)
                    dg.deserialize_value(
                        DagsterGrpcClient(port=port).list_repositories(), ListRepositoriesResponse
                    )

                finally:
                    client.shutdown_server()
                    process.communicate(timeout=30)


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_streaming(entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = entrypoint + [
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(subprocess_args)

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


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_sensor_timeout(entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = entrypoint + [
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(subprocess_args)

    try:
        wait_for_grpc_server(
            process, DagsterGrpcClient(port=port, host="localhost"), subprocess_args
        )
        client = DagsterGrpcClient(port=port)

        with dg.instance_for_test() as instance:
            repo_origin = RemoteRepositoryOrigin(
                code_location_origin=GrpcServerCodeLocationOrigin(port=port, host="localhost"),
                repository_name="bar_repo",
            )
            with pytest.raises(DagsterUserCodeUnreachableError) as exc_info:
                client.external_sensor_execution(
                    sensor_execution_args=SensorExecutionArgs(
                        repository_origin=repo_origin,
                        instance_ref=instance.get_ref(),
                        sensor_name="slow_sensor",
                        last_tick_completion_time=None,
                        last_run_key=None,
                        cursor=None,
                        timeout=2,
                        last_sensor_start_time=None,
                    ),
                )

            assert "Deadline Exceeded" in str(exc_info.getrepr())

            # Call succeeds without the timeout
            client.external_sensor_execution(
                sensor_execution_args=SensorExecutionArgs(
                    repository_origin=repo_origin,
                    instance_ref=instance.get_ref(),
                    sensor_name="slow_sensor",
                    last_tick_completion_time=None,
                    last_run_key=None,
                    cursor=None,
                    last_sensor_start_time=None,
                ),
            )
    finally:
        process.terminate()
        process.wait()


@pytest.mark.parametrize("entrypoint", entrypoints())
def test_load_with_container_context(entrypoint):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    container_context = {
        "k8s": {
            "image_pull_policy": "Never",
            "image_pull_secrets": [{"name": "your_secret"}],
        }
    }

    subprocess_args = entrypoint + [
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
        assert client.ping("foobar") == {
            "echo": "foobar",
            "serialized_server_utilization_metrics": "",
        }

        list_repositories_response = sync_list_repositories_grpc(client)
        assert list_repositories_response.entry_point == ["dagster"]
        assert list_repositories_response.executable_path == sys.executable
        assert list_repositories_response.container_context == container_context
        assert list_repositories_response.dagster_library_versions == {
            "dagster": dagster_version,
            "dagster-shared": dagster_shared_version,
        }

    finally:
        process.terminate()
        process.wait()


def test_load_with_error_logging(capfd):
    port = find_free_port()
    python_file = dg.file_relative_path(__file__, "grpc_repo.py")

    subprocess_args = ["dagster", "api", "grpc"] + [
        "--port",
        str(port),
        "--python-file",
        python_file,
    ]

    process = subprocess.Popen(
        subprocess_args,
        env={**os.environ, "DAGSTER_CODE_SERVER_LOG_EXCEPTIONS": "1"},
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    try:
        client = DagsterGrpcClient(port=port, host="localhost")

        wait_for_grpc_server(process, client, subprocess_args)

        missing_job_origin = RemoteJobOrigin(
            job_name="missing_job_name",
            repository_origin=RemoteRepositoryOrigin(
                repository_name="missing_repo_name",
                code_location_origin=RegisteredCodeLocationOrigin(
                    location_name="missing_location_name"
                ),
            ),
        )

        result = dg.deserialize_value(
            client.external_pipeline_subset(
                pipeline_subset_snapshot_args=JobSubsetSnapshotArgs(
                    job_origin=missing_job_origin,
                    op_selection=None,
                ),
            )
        )

        assert result.error  # ty: ignore[unresolved-attribute]
        assert 'Could not find a repository called "missing_repo_name"' in str(result.error)  # ty: ignore[unresolved-attribute]

    finally:
        process.terminate()
        process.wait()

    out, _err = capfd.readouterr()

    assert 'Could not find a repository called "missing_repo_name"' in out
