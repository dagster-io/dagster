from typing import TYPE_CHECKING

import dagster._check as check
from dagster.core.errors import DagsterUserCodeProcessError
from dagster.utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster.grpc.client import DagsterGrpcClient


def sync_get_server_id(api_client: "DagsterGrpcClient") -> str:
    from dagster.grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)
    result = check.inst(api_client.get_server_id(), (str, SerializableErrorInfo))
    if isinstance(result, SerializableErrorInfo):
        raise DagsterUserCodeProcessError(
            result.to_string(), user_code_process_error_infos=[result]
        )
    else:
        return result
