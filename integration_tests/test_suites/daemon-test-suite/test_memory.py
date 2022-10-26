import inspect
import os
import time
from contextlib import contextmanager

import objgraph

from dagster import job, op, RunRequest, repository, schedule, sensor
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.load_target import PythonFileTarget
from dagster._daemon.controller import daemon_controller_from_instance


@op()
def foo_op(_):
    pass


@job
def foo_job():
    foo_op()


@job
def other_foo_job():
    foo_op()


@schedule(
    job_name="foo_job",
    cron_schedule="*/1 * * * *",
)
def always_run_schedule(_context):
    return {}


@sensor(job_name="foo_job", minimum_interval_seconds=10)
def always_on_sensor(_context):
    return RunRequest(run_key=None, run_config={}, tags={})


@repository
def example_repo():
    return [foo_job, always_run_schedule, always_on_sensor]


@contextmanager
def get_example_repository_location(instance):
    load_target = workspace_load_target()
    origin = load_target.create_origins()[0]

    with origin.create_single_location(instance) as location:
        yield location


def workspace_load_target():
    return PythonFileTarget(
        python_file=__file__,
        attribute=None,
        working_directory=os.path.dirname(__file__),
        location_name=None,
    )


@contextmanager
def get_example_repo(instance):
    with get_example_repository_location(instance) as location:
        yield location.get_repository("example_repo")


def test_no_memory_leaks():
    with instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator",
                "class": "QueuedRunCoordinator",
            },
            "run_launcher": {
                "class": "DefaultRunLauncher",
                "module": "dagster.core.launcher.default_run_launcher",
                "config": {
                    "wait_for_processes": False,
                },
            },
        }
    ) as instance:
        with get_example_repo(instance) as repo:

            external_schedule = repo.get_external_schedule("always_run_schedule")
            external_sensor = repo.get_external_sensor("always_on_sensor")

            instance.start_schedule(external_schedule)
            instance.start_sensor(external_sensor)

            with daemon_controller_from_instance(
                instance,
                workspace_load_target=workspace_load_target(),
                wait_for_processes_on_exit=True,
            ) as controller:
                start_time = time.time()

                growth = objgraph.growth(
                    limit=10,
                    filter=lambda obj: inspect.getmodule(obj)
                    and "dagster" in inspect.getmodule(obj).__name__,
                )
                while True:
                    time.sleep(30)

                    controller.check_daemon_threads()
                    controller.check_daemon_heartbeats()

                    growth = objgraph.growth(
                        limit=10,
                        filter=lambda obj: inspect.getmodule(obj)
                        and "dagster" in inspect.getmodule(obj).__name__,
                    )
                    if not growth:
                        print(  # pylint: disable=print-call
                            f"Memory stopped growing after {int(time.time() - start_time)} seconds"
                        )
                        break

                    if (time.time() - start_time) > 300:
                        raise Exception(
                            "Memory still growing after 5 minutes. Most recent growth: "
                            + str(growth)
                        )

                    print("Growth: " + str(growth))  # pylint: disable=print-call
