import os
import sys
import time
from contextlib import ExitStack

import pytest
from dagster.serdes.ipc import (
    interrupt_ipc_subprocess,
    interrupt_ipc_subprocess_pid,
    open_ipc_subprocess,
)
from dagster.utils import file_relative_path, process_is_alive, safe_tempfile_path


def wait_for_file(path, timeout=5):
    interval = 0.1
    total_time = 0
    while not os.path.exists(path) and total_time < timeout:
        time.sleep(interval)
        total_time += interval
    if total_time >= timeout:
        raise Exception("wait_for_file: timeout")
    time.sleep(interval)


def wait_for_process(pid, timeout=5):
    interval = 0.1
    total_time = 0
    while process_is_alive(pid) and total_time < timeout:
        time.sleep(interval)
        total_time += interval
    if total_time >= timeout:
        raise Exception("wait_for_process: timeout")
    # The following line can be removed to reliably provoke failures on Windows -- hypothesis
    # is that there's a race in psutil.Process which tells us a process is gone before it stops
    # contending for files
    time.sleep(interval)


@pytest.fixture(scope="function")
def windows_legacy_stdio_env():
    old_env_value = os.getenv("PYTHONLEGACYWINDOWSSTDIO")
    try:
        os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
        yield
    finally:
        if old_env_value is not None:
            os.environ["PYTHONLEGACYWINDOWSSTDIO"] = old_env_value
        else:
            del os.environ["PYTHONLEGACYWINDOWSSTDIO"]


def test_interrupt_ipc_subprocess():
    with safe_tempfile_path() as started_sentinel:
        with safe_tempfile_path() as interrupt_sentinel:
            sleepy_process = open_ipc_subprocess(
                [
                    sys.executable,
                    file_relative_path(__file__, "subprocess_with_interrupt_support.py"),
                    started_sentinel,
                    interrupt_sentinel,
                ]
            )
            wait_for_file(started_sentinel)
            interrupt_ipc_subprocess(sleepy_process)
            wait_for_file(interrupt_sentinel)
            with open(interrupt_sentinel, "r") as fd:
                assert fd.read().startswith("received_keyboard_interrupt")


def test_interrupt_ipc_subprocess_by_pid():
    with safe_tempfile_path() as started_sentinel:
        with safe_tempfile_path() as interrupt_sentinel:
            sleepy_process = open_ipc_subprocess(
                [
                    sys.executable,
                    file_relative_path(__file__, "subprocess_with_interrupt_support.py"),
                    started_sentinel,
                    interrupt_sentinel,
                ]
            )
            wait_for_file(started_sentinel)
            interrupt_ipc_subprocess_pid(sleepy_process.pid)
            wait_for_file(interrupt_sentinel)
            with open(interrupt_sentinel, "r") as fd:
                assert fd.read().startswith("received_keyboard_interrupt")


def test_interrupt_ipc_subprocess_grandchild():
    with ExitStack() as context_stack:
        (
            child_opened_sentinel,
            parent_interrupt_sentinel,
            child_started_sentinel,
            child_interrupt_sentinel,
        ) = [context_stack.enter_context(safe_tempfile_path()) for _ in range(4)]
        child_process = open_ipc_subprocess(
            [
                sys.executable,
                file_relative_path(__file__, "parent_subprocess_with_interrupt_support.py"),
                child_opened_sentinel,
                parent_interrupt_sentinel,
                child_started_sentinel,
                child_interrupt_sentinel,
            ]
        )
        wait_for_file(child_opened_sentinel)
        wait_for_file(child_started_sentinel)
        interrupt_ipc_subprocess(child_process)
        wait_for_file(child_interrupt_sentinel)
        with open(child_interrupt_sentinel, "r") as fd:
            assert fd.read().startswith("received_keyboard_interrupt")
        wait_for_file(parent_interrupt_sentinel)
        with open(parent_interrupt_sentinel, "r") as fd:
            assert fd.read().startswith("parent_received_keyboard_interrupt")


def test_interrupt_compute_log_tail_child(
    windows_legacy_stdio_env,  # pylint: disable=redefined-outer-name, unused-argument
):
    with ExitStack() as context_stack:
        (stdout_pids_file, stderr_pids_file, opened_sentinel, interrupt_sentinel) = [
            context_stack.enter_context(safe_tempfile_path()) for _ in range(4)
        ]

        child_process = open_ipc_subprocess(
            [
                sys.executable,
                file_relative_path(__file__, "compute_log_subprocess.py"),
                stdout_pids_file,
                stderr_pids_file,
                opened_sentinel,
                interrupt_sentinel,
            ]
        )
        wait_for_file(opened_sentinel)
        wait_for_file(stdout_pids_file)
        wait_for_file(stderr_pids_file)

        with open(opened_sentinel, "r") as opened_sentinel_fd:
            assert opened_sentinel_fd.read().startswith("opened_compute_log_subprocess")

        with open(stdout_pids_file, "r") as stdout_pids_fd:
            stdout_pids_str = stdout_pids_fd.read()
            assert stdout_pids_str.startswith("stdout pids:")
            stdout_pids = list(
                map(
                    lambda x: int(x) if x != "None" else None,
                    [x.strip("(),") for x in stdout_pids_str.split(" ")[2:]],
                )
            )

        with open(stderr_pids_file, "r") as stderr_pids_fd:
            stderr_pids_str = stderr_pids_fd.read()
            assert stderr_pids_str.startswith("stderr pids:")
            stderr_pids = list(
                map(
                    lambda x: int(x) if x != "None" else None,
                    [x.strip("(),") for x in stderr_pids_str.split(" ")[2:]],
                )
            )

        interrupt_ipc_subprocess(child_process)

        for stdout_pid in stdout_pids:
            if stdout_pid is not None:
                wait_for_process(stdout_pid)

        for stderr_pid in stderr_pids:
            if stderr_pid is not None:
                wait_for_process(stderr_pid)

        wait_for_file(interrupt_sentinel)

        with open(interrupt_sentinel, "r") as fd:
            assert fd.read().startswith("compute_log_subprocess_interrupt")


def test_segfault_compute_log_tail(
    windows_legacy_stdio_env,  # pylint: disable=redefined-outer-name, unused-argument
):
    with safe_tempfile_path() as stdout_pids_file:
        with safe_tempfile_path() as stderr_pids_file:
            child_process = open_ipc_subprocess(
                [
                    sys.executable,
                    file_relative_path(__file__, "compute_log_subprocess_segfault.py"),
                    stdout_pids_file,
                    stderr_pids_file,
                ]
            )

            child_process.wait()

            wait_for_file(stdout_pids_file)
            with open(stdout_pids_file, "r") as stdout_pids_fd:
                stdout_pids_str = stdout_pids_fd.read()
                assert stdout_pids_str.startswith("stdout pids:")
                stdout_pids = list(
                    map(
                        lambda x: int(x) if x != "None" else None,
                        stdout_pids_str.split(" ")[-1].strip("()").split(","),
                    )
                )

            wait_for_file(stderr_pids_file)
            with open(stderr_pids_file, "r") as stderr_pids_fd:
                stderr_pids_str = stderr_pids_fd.read()
                assert stderr_pids_str.startswith("stderr pids:")
                stderr_pids = list(
                    map(
                        lambda x: int(x) if x != "None" else None,
                        stderr_pids_str.split(" ")[-1].strip("()").split(","),
                    )
                )

            for stdout_pid in stdout_pids:
                if stdout_pid is not None:
                    wait_for_process(stdout_pid)

            for stderr_pid in stderr_pids:
                if stderr_pid is not None:
                    wait_for_process(stderr_pid)


def test_interrupt_compute_log_tail_grandchild(
    windows_legacy_stdio_env,  # pylint: disable=redefined-outer-name, unused-argument
):
    with ExitStack() as context_stack:
        (
            child_opened_sentinel,
            parent_interrupt_sentinel,
            child_started_sentinel,
            stdout_pids_file,
            stderr_pids_file,
            child_interrupt_sentinel,
        ) = [context_stack.enter_context(safe_tempfile_path()) for _ in range(6)]

        parent_process = open_ipc_subprocess(
            [
                sys.executable,
                file_relative_path(__file__, "parent_compute_log_subprocess.py"),
                child_opened_sentinel,
                parent_interrupt_sentinel,
                child_started_sentinel,
                stdout_pids_file,
                stderr_pids_file,
                child_interrupt_sentinel,
            ]
        )

        wait_for_file(child_opened_sentinel)
        wait_for_file(child_started_sentinel)

        wait_for_file(stdout_pids_file)
        with open(stdout_pids_file, "r") as stdout_pids_fd:
            stdout_pids_str = stdout_pids_fd.read()
            assert stdout_pids_str.startswith("stdout pids:")
            stdout_pids = list(
                map(
                    lambda x: int(x) if x != "None" else None,
                    [x.strip("(),") for x in stdout_pids_str.split(" ")[2:]],
                )
            )

        wait_for_file(stderr_pids_file)
        with open(stderr_pids_file, "r") as stderr_pids_fd:
            stderr_pids_str = stderr_pids_fd.read()
            assert stderr_pids_str.startswith("stderr pids:")
            stderr_pids = list(
                map(
                    lambda x: int(x) if x != "None" else None,
                    [x.strip("(),") for x in stderr_pids_str.split(" ")[2:]],
                )
            )

        interrupt_ipc_subprocess(parent_process)

        wait_for_file(child_interrupt_sentinel)
        with open(child_interrupt_sentinel, "r") as fd:
            assert fd.read().startswith("compute_log_subprocess_interrupt")

        wait_for_file(parent_interrupt_sentinel)
        with open(parent_interrupt_sentinel, "r") as fd:
            assert fd.read().startswith("parent_received_keyboard_interrupt")

        for stdout_pid in stdout_pids:
            if stdout_pid is not None:
                wait_for_process(stdout_pid)

        for stderr_pid in stderr_pids:
            if stderr_pid is not None:
                wait_for_process(stderr_pid)
