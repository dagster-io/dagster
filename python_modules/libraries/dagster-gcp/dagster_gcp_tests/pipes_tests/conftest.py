import os
import time
from collections.abc import Iterable

import pytest
from gcp_storage_emulator.server import create_server
from google.cloud import exceptions
from google.cloud.storage import Client as GCSClient

from dagster_gcp_tests.pipes_tests.utils import temp_script

GCS_SERVER_URL = "http://localhost:9023"
GCS_BUCKET = "dagster-pipes"


@pytest.fixture
def gcs_bucket() -> Iterable[str]:
    server = create_server("localhost", 9023, in_memory=False, default_bucket=GCS_BUCKET)
    server.start()
    time.sleep(0.1)
    yield GCS_BUCKET
    server.stop()


@pytest.fixture
def gcs_client(gcs_bucket: str) -> GCSClient:
    os.environ["STORAGE_EMULATOR_HOST"] = GCS_SERVER_URL
    client = GCSClient()
    try:
        client.create_bucket(GCS_BUCKET)
    except exceptions.Conflict:
        pass
    yield client
    del os.environ["STORAGE_EMULATOR_HOST"]


@pytest.fixture
def external_script() -> Iterable[str]:
    # This is called in an external process and so cannot access outer scope
    def script_fn():
        import os  # noqa
        import time

        import argparse

        from google.cloud.storage import Client as GCSClient
        from dagster_pipes import (
            PipesGCSContextLoader,
            PipesGCSMessageWriter,
            open_dagster_pipes,
            PipesCliArgsParamsLoader,
            PipesEnvVarParamsLoader,
        )

        # this url has to be hardcoded because it's an external script
        os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:9023"
        gcs_client = GCSClient()

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--context-loader", help="context loader", default=None, required=False, type=str
        )
        parser.add_argument(
            "--message-writer", help="message writer", default=None, required=False, type=str
        )
        parser.add_argument(
            "--params-loader", help="params loader", default=None, required=False, type=str
        )

        args = parser.parse_args()

        context_loader = None
        if args.context_loader and args.context_loader == "gcs":
            context_loader = PipesGCSContextLoader(client=gcs_client)

        message_writer = None
        if args.message_writer and args.message_writer == "gcs":
            message_writer = PipesGCSMessageWriter(client=gcs_client, interval=0.001)

        params_loader = PipesEnvVarParamsLoader()
        if args.params_loader and args.params_loader == "cli":
            params_loader = PipesCliArgsParamsLoader()

        with open_dagster_pipes(
            context_loader=context_loader,
            message_writer=message_writer,
            params_loader=params_loader,
        ) as context:
            context.log.info("hello world")
            context.report_asset_materialization(
                metadata={"bar": {"raw_value": context.get_extra("bar"), "type": "text"}},
                data_version="alpha",
            )
            time.sleep(0.1)  # sleep to make sure that we encompass multiple intervals for GCS IO

    with temp_script(script_fn) as script_path:
        yield script_path
