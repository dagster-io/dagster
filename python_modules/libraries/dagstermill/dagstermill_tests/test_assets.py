import importlib.util
import os
import pickle
import tempfile
from contextlib import contextmanager

import nbformat
import pytest
from dagstermill import DagstermillError
from dagstermill.compat import ExecutionError
from dagstermill.factory import define_dagstermill_solid
# from dagstermill.examples.repository import notebook_assets_repo
from jupyter_client.kernelspec import NoSuchKernel
from nbconvert.preprocessors import ExecutePreprocessor
from dagster._core.definitions.reconstruct import ReconstructablePipeline

from dagster._check import CheckError
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata import NotebookMetadataValue, PathMetadataValue
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline, pipeline
from dagster._utils import file_relative_path, safe_tempfile_path
from dagster import AssetKey, reconstructable, define_asset_job, AssetSelection

DAGSTER_PANDAS_PRESENT = importlib.util.find_spec("dagster_pandas") is not None
SKLEARN_PRESENT = importlib.util.find_spec("sklearn") is not None
MATPLOTLIB_PRESENT = importlib.util.find_spec("matplotlib") is not None


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.entry_data, (NotebookMetadataValue, PathMetadataValue)):
            return metadata_entry.entry_data.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.step_event_list if x.event_type_value == "ASSET_MATERIALIZATION"
    ]
    for materialization_event in materialization_events:
        result_path = get_path(materialization_event)
        if os.path.exists(result_path):
            os.unlink(result_path)


@contextmanager
def exec_for_test(job_name, env=None, raise_on_error=True, **kwargs):
    result = None
    recon_pipeline = ReconstructablePipeline.for_module("dagstermill.examples.repository", job_name)

    with instance_for_test() as instance:
        try:
            result = execute_pipeline(
                recon_pipeline,
                env,
                instance=instance,
                raise_on_error=raise_on_error,
                **kwargs,
            )
            yield result
        finally:
            if result:
                cleanup_result_notebook(result)


@pytest.mark.notebook_test
def test_hello_world():
    with exec_for_test("hello_world_asset_job") as result:
        assert result.success

@pytest.mark.notebook_test
def test_hello_world_with_custom_tags_and_description_asset():
    with exec_for_test("hello_world_with_custom_tags_and_description_asset_job") as result:
        assert result.success

@pytest.mark.notebook_test
def test_hello_world_config_asset():
    with exec_for_test("hello_world_config_asset_job") as result:
        assert result.success

@pytest.mark.notebook_test
def test_goodbye_config_asset():
    with exec_for_test("goodbye_config_asset_job") as result:
        assert result.success

@pytest.mark.notebook_test
def test_hello_logging_asset():
    with exec_for_test("hello_logging_asset_job") as result:
        assert result.success


@pytest.mark.notebook_test
def test_add_two_number_asset():
    with exec_for_test("add_two_number_asset_job") as result:
        assert result.success

@pytest.mark.notebook_test
def test_hello_world_resource_asset():
    with exec_for_test("hello_world_resource_asset_job") as result:
        assert result.success


