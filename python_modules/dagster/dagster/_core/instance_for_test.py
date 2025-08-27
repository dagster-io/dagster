import os
import sys
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from typing import Any, Optional

import yaml

from dagster._annotations import public
from dagster._core.instance import DagsterInstance
from dagster._utils.env import environ
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.merger import merge_dicts


@public
@contextmanager
def instance_for_test(
    overrides: Optional[Mapping[str, Any]] = None,
    set_dagster_home: bool = True,
    temp_dir: Optional[str] = None,
    synchronous_run_coordinator: bool = False,
    synchronous_run_launcher: bool = False,
) -> Iterator[DagsterInstance]:
    """Creates a persistent :py:class:`~dagster.DagsterInstance` available within a context manager.

    When a context manager is opened, if no `temp_dir` parameter is set, a new
    temporary directory will be created for the duration of the context
    manager's opening. If the `set_dagster_home` parameter is set to True
    (True by default), the `$DAGSTER_HOME` environment variable will be
    overridden to be this directory (or the directory passed in by `temp_dir`)
    for the duration of the context manager being open.

    Args:
        overrides (Optional[Mapping[str, Any]]):
            Config to provide to instance (config format follows that typically found in an `instance.yaml` file).
        set_dagster_home (Optional[bool]):
            If set to True, the `$DAGSTER_HOME` environment variable will be
            overridden to be the directory used by this instance for the
            duration that the context manager is open. Upon the context
            manager closing, the `$DAGSTER_HOME` variable will be re-set to the original value. (Defaults to True).
        temp_dir (Optional[str]):
            The directory to use for storing local artifacts produced by the
            instance. If not set, a temporary directory will be created for
            the duration of the context manager being open, and all artifacts
            will be torn down afterward.
    """
    with ExitStack() as stack:
        if not temp_dir:
            temp_dir = stack.enter_context(tempfile.TemporaryDirectory())

        # wait for any grpc processes that created runs during test disposal to finish,
        # since they might also be using this instance's tempdir (and to keep each test
        # isolated / avoid race conditions in newer versions of grpcio when servers are
        # shutting down and spinning up at the same time)
        instance_overrides = merge_dicts(
            {
                "telemetry": {"enabled": False},
                "code_servers": {"wait_for_local_processes_on_shutdown": True},
            },
            {
                "run_coordinator": {
                    "module": "dagster._core.run_coordinator.sync_in_memory_run_coordinator",
                    "class": "SyncInMemoryRunCoordinator",
                },
            }
            if synchronous_run_coordinator
            else {},
            {
                "run_launcher": {
                    "module": "dagster._core.launcher.sync_in_memory_run_launcher",
                    "class": "SyncInMemoryRunLauncher",
                },
            }
            if synchronous_run_launcher
            else {},
            (overrides if overrides else {}),
        )

        if set_dagster_home:
            stack.enter_context(
                environ({"DAGSTER_HOME": temp_dir, "DAGSTER_DISABLE_TELEMETRY": "yes"})
            )

        with open(os.path.join(temp_dir, "dagster.yaml"), "w", encoding="utf8") as fd:
            yaml.dump(instance_overrides, fd, default_flow_style=False)

        with DagsterInstance.from_config(temp_dir) as instance:
            try:
                yield instance
            except:
                sys.stderr.write(
                    "Test raised an exception, attempting to clean up instance:"
                    + serializable_error_info_from_exc_info(sys.exc_info()).to_string()
                    + "\n"
                )
                raise
            finally:
                cleanup_test_instance(instance)


def cleanup_test_instance(instance: DagsterInstance) -> None:
    # To avoid filesystem contention when we close the temporary directory, wait for
    # all runs to reach a terminal state, and close any subprocesses or threads
    # that might be accessing the run history DB.

    # Since launcher is lazy loaded, we don't need to do anyting if it's None
    if instance._run_launcher:  # noqa: SLF001
        instance._run_launcher.join()  # noqa: SLF001
