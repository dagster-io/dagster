from dagster import check


def sync_get_streaming_external_notebook_data_grpc(api_client, notebook_path):
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    check.str_param(notebook_path, "notebook_path")

    result = api_client.external_notebook_data(notebook_path=notebook_path)

    return result
