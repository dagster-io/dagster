from dagster import check
from dagster.core.host_representation.external_data import ExternalNotebookData
from dagster.grpc.types import NotebookDataArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple


def sync_get_streaming_external_notebook_data_grpc(api_client, notebook_path):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.str_param(notebook_path, "notebook_path")

    result = check.inst(
        deserialize_json_to_dagster_namedtuple(
            api_client.external_notebook_data(
                notebook_data_args=NotebookDataArgs(notebook_path=notebook_path),
            )
        ),
        ExternalNotebookData,
    )

    return result
