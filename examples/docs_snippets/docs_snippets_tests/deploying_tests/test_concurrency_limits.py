import os

from dagster._core.instance.ref import InstanceRef
from dagster._core.run_coordinator import QueuedRunCoordinator
from docs_snippets.deploying.concurrency_limits.concurrency_limits import (
    important_job,
    less_important_schedule,
)


def test_inclusion():
    assert important_job
    assert less_important_schedule


def test_instance_yaml(docs_snippets_folder):
    intance_yaml_folder = os.path.join(
        docs_snippets_folder,
        "deploying",
        "concurrency_limits",
    )
    assert isinstance(
        InstanceRef.from_dir(intance_yaml_folder).run_coordinator, QueuedRunCoordinator
    )


def test_unique_value_instance_yaml(docs_snippets_folder):
    intance_yaml_folder = os.path.join(
        docs_snippets_folder,
        "deploying",
        "concurrency_limits",
    )
    assert isinstance(
        InstanceRef.from_dir(
            intance_yaml_folder, config_filename="per-unique-value-dagster.yaml"
        ).run_coordinator,
        QueuedRunCoordinator,
    )
