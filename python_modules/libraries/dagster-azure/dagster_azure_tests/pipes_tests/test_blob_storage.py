import tempfile

import dagster as dg
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

from dagster_azure_tests.pipes_tests.mock_blob_storage import MockBlobServiceClient
from dagster_azure_tests.pipes_tests.utils import _PYTHON_EXECUTABLE


def test_blob_storage_injector_and_messagewriter(
    storage_account_name, container_name, external_script
):
    blob_storage_service_client = MockBlobServiceClient(tempfile.gettempdir(), storage_account_name)
    blob_storage_service_client.cleanup()  # Make sure there is no data from older test runs
    try:
        context_injector = PipesAzureBlobStorageContextInjector(
            container=container_name, client=blob_storage_service_client
        )  # pyright: ignore
        message_reader = PipesAzureBlobStorageMessageReader(
            container=container_name, client=blob_storage_service_client, interval=0.001
        )  # pyright: ignore

        @dg.asset(check_specs=[dg.AssetCheckSpec(name="foo_check", asset=dg.AssetKey(["foo"]))])
        def foo(context: dg.AssetExecutionContext, ext: dg.PipesSubprocessClient):
            return ext.run(
                command=[_PYTHON_EXECUTABLE, external_script],
                context=context,
                extras={"bar": "baz"},
                env={},
            ).get_results()

        resource = dg.PipesSubprocessClient(
            context_injector=context_injector, message_reader=message_reader
        )

        with dg.instance_for_test() as instance:
            dg.materialize([foo], instance=instance, resources={"ext": resource})
            mat = instance.get_latest_materialization_event(foo.key)
            assert mat and mat.asset_materialization
            assert isinstance(mat.asset_materialization.metadata["bar"], MarkdownMetadataValue)
            assert mat.asset_materialization.metadata["bar"].value == "baz"
            assert mat.asset_materialization.tags
            assert mat.asset_materialization.tags[DATA_VERSION_TAG] == "alpha"
            assert mat.asset_materialization.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

            asset_check_executions = instance.event_log_storage.get_asset_check_execution_history(
                check_key=AssetCheckKey(foo.key, name="foo_check"),
                limit=1,
            )
            assert len(asset_check_executions) == 1
            assert asset_check_executions[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED
    finally:
        blob_storage_service_client.cleanup()
