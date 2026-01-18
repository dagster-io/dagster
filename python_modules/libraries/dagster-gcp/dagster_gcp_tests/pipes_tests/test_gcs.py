import json
import uuid
from typing import Optional

import dagster as dg
import pytest
from dagster_gcp.pipes import PipesGCSContextInjector, PipesGCSMessageReader
from dagster_pipes import (
    PIPES_PROTOCOL_VERSION,
    PIPES_PROTOCOL_VERSION_FIELD,
    PipesGCSMessageWriter,
)
from google.cloud.storage import Client as GCSClient

from dagster_gcp_tests.pipes_tests.utils import _PYTHON_EXECUTABLE


def test_message_writer(gcs_bucket: str, gcs_client: GCSClient):
    message_writer = PipesGCSMessageWriter(client=gcs_client)

    key_prefix = str(uuid.uuid4())

    with message_writer.open({"bucket": gcs_bucket, "key_prefix": key_prefix}) as channel:
        channel.write_message(
            {
                PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
                "method": "report_custom_message",
                "params": {"payload": {"foo": "bar"}},
            }
        )

    assert len(list(gcs_client.list_blobs(gcs_bucket, prefix=key_prefix))) == 1

    blob = next(gcs_client.list_blobs(gcs_bucket, prefix=key_prefix))

    assert json.loads(blob.download_as_string()) == {
        PIPES_PROTOCOL_VERSION_FIELD: PIPES_PROTOCOL_VERSION,
        "method": "report_custom_message",
        "params": {"payload": {"foo": "bar"}},
    }


@pytest.mark.parametrize(
    "context_loader",
    [None, "gcs"],
)
def test_complete(
    gcs_bucket: str, gcs_client: GCSClient, external_script: str, context_loader: Optional[str]
):
    @dg.asset
    def my_asset(context: dg.AssetExecutionContext, pipes_client: dg.PipesSubprocessClient):
        cmd = [_PYTHON_EXECUTABLE, external_script, "--message-writer", "gcs"]

        if context_loader:
            cmd.extend(["--context-loader", context_loader])

        return pipes_client.run(command=cmd, context=context, extras={"bar": "baz"}).get_results()

    message_reader = PipesGCSMessageReader(
        bucket=gcs_bucket,
        client=gcs_client,
    )

    context_injector = (
        PipesGCSContextInjector(
            client=gcs_client,
            bucket=gcs_bucket,
        )
        if context_loader == "gcs"
        else None
    )

    pipes_client = dg.PipesSubprocessClient(
        message_reader=message_reader,
        context_injector=context_injector,
    )

    with dg.instance_for_test() as instance:
        result = dg.materialize(
            [my_asset],
            instance=instance,
            resources={"pipes_client": pipes_client},
            raise_on_error=False,
        )
        assert result.success
        mat = instance.get_latest_materialization_event(my_asset.key)
        assert mat and mat.asset_materialization
        assert mat.asset_materialization.metadata["bar"] == dg.MetadataValue.text("baz")
