import os
from contextlib import contextmanager

from dagster import execute_job
from dagster._core.definitions.metadata import NotebookMetadataValue, PathMetadataValue
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.test_utils import instance_for_test


def get_path(materialization_event):
    for value in materialization_event.event_specific_data.materialization.metadata.values():
        if isinstance(value, (PathMetadataValue, NotebookMetadataValue)):
            return value.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.all_events if x.event_type_value == "ASSET_MATERIALIZATION"
    ]
    for materialization_event in materialization_events:
        result_path = get_path(materialization_event)
        if os.path.exists(result_path):  # pyright: ignore[reportArgumentType]
            os.unlink(result_path)  # pyright: ignore[reportArgumentType]


@contextmanager
def exec_for_test(fn_name, env=None, raise_on_error=True, **kwargs):
    result = None
    recon_job = ReconstructableJob.for_module("dagstermill.examples.repository", fn_name)

    with instance_for_test() as instance:
        try:
            with execute_job(
                job=recon_job,
                run_config=env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            ) as result:
                yield result
        finally:
            if result:
                cleanup_result_notebook(result)
