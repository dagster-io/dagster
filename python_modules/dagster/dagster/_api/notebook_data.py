from typing import TYPE_CHECKING

import dagster._check as check

if TYPE_CHECKING:
    from dagster._grpc.client import DagsterGrpcClient


def sync_get_streaming_external_notebook_data_grpc(
    api_client: "DagsterGrpcClient", notebook_path: str
):
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.str_param(notebook_path, "notebook_path")

    result = api_client.external_notebook_data(notebook_path=notebook_path)

    return result
