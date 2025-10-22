import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import dagster as dg
from azure.ai.ml import command
from azure.ai.ml.entities import Command
from dagster import AssetCheckKey
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.definitions.metadata import MarkdownMetadataValue
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster_azure.pipes import (
    PipesAzureBlobStorageContextInjector,
    PipesAzureBlobStorageMessageReader,
)
from dagster_azure.pipes.clients.azureml import PipesAzureMLClient

from dagster_azure_tests.pipes_tests.mock_blob_storage import MockBlobServiceClient
from dagster_azure_tests.pipes_tests.utils import _PYTHON_EXECUTABLE


class MockAzureMLJob:
    def __init__(self, name: str, command: Command):
        self.name = name
        self.command = command
        cmd_parts = self.command.component.command.split()  # pyright: ignore
        cmd_parts[0] = _PYTHON_EXECUTABLE
        env = {**self.command.environment_variables} if self.command.environment_variables else {}

        self._process = subprocess.Popen(
            cmd_parts,
            env={**os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @property
    def status(self):
        if self._process.poll() is None:
            return "Running"
        elif self._process.poll() == 0:
            return "Completed"
        else:
            return "Failed"


class MockAzureMLClient:
    """Mock Azure ML Client for testing."""

    def __init__(self):
        self._jobs = {}
        self._job_counter = 0

    def create_or_update(self, command: Command) -> MockAzureMLJob:
        """Simulates an Azure ML job by running a subprocess."""
        self._job_counter += 1
        job_name = f"mock_job_{self._job_counter}"
        job = MockAzureMLJob(job_name, command)
        self._jobs[job_name] = job

        return job

    @property
    def jobs(self):
        """Return a mock jobs object with get method."""
        mock_jobs = MagicMock()

        def get_job(job_name):
            return self._jobs.get(job_name)

        mock_jobs.get = get_job
        mock_jobs.begin_cancel = MagicMock()
        return mock_jobs


def test_azureml_pipes(storage_account_name, container_name, external_script):
    """Test Azure ML pipes client with blob storage."""
    blob_storage_service_client = MockBlobServiceClient(tempfile.gettempdir(), storage_account_name)
    blob_storage_service_client.cleanup()  # Clean up any data from previous runs

    try:
        context_injector = PipesAzureBlobStorageContextInjector(
            container=container_name,
            client=blob_storage_service_client,  # pyright: ignore
        )
        message_reader = PipesAzureBlobStorageMessageReader(
            container=container_name,
            client=blob_storage_service_client,  # pyright: ignore[reportArgumentType]
            interval=0.001,
        )
        azureml_client = MockAzureMLClient()

        @dg.asset(
            check_specs=[dg.AssetCheckSpec(name="foo_check", asset=dg.AssetKey(["azureml_asset"]))]
        )
        def azureml_asset(context: dg.AssetExecutionContext):
            return (
                PipesAzureMLClient(
                    azureml_client,  # pyright: ignore
                    context_injector=context_injector,
                    message_reader=message_reader,
                    poll_interval_seconds=0.1,
                )
                .run(
                    context=context,
                    extras={"bar": "baz"},
                    command=command(
                        code=str(Path(external_script).parent),
                        command=f"{_PYTHON_EXECUTABLE} {external_script}",
                        environment="dagster-env:1",
                        display_name="test_azureml_job",
                        compute="test_compute",
                    ),
                )
                .get_results()
            )

        with dg.instance_for_test() as instance:
            result = dg.materialize([azureml_asset], instance=instance)
            assert result.success

            mat = instance.get_latest_materialization_event(azureml_asset.key)
            assert mat and mat.asset_materialization
            assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
            assert mat.asset_materialization.metadata["bar"].value == "baz"
            assert mat.asset_materialization.tags
            assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
            assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

            asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
                check_key=AssetCheckKey(azureml_asset.key, name="foo_check"),
                limit=1,
            )
            assert len(asset_check_executions) == 1
            assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED
    finally:
        blob_storage_service_client.cleanup()
