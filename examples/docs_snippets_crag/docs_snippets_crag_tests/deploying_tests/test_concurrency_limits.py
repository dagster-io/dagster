import os

from dagster.core.instance.ref import InstanceRef
from dagster.core.run_coordinator import QueuedRunCoordinator
from docs_snippets_crag.deploying.concurrency_limits.concurrency_limits import (  # pylint: disable=import-error
    important_pipeline,
    less_important_schedule,
)


def test_inclusion():
    assert important_pipeline
    assert less_important_schedule


def test_instance_yaml(docs_snippets_crag_folder):
    intance_yaml_folder = os.path.join(
        docs_snippets_crag_folder,
        "deploying",
        "concurrency_limits",
    )
    assert isinstance(
        InstanceRef.from_dir(intance_yaml_folder).run_coordinator, QueuedRunCoordinator
    )
