from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.errors import DagsterUserCodeProcessError
from dagster._serdes import deserialize_value, serialize_value
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster_shared.serdes.objects import DefsStateInfo

    from dagster._grpc.client import DagsterGrpcClient


def sync_reload_code_with_state_grpc(
    api_client: "DagsterGrpcClient", defs_state_info: "DefsStateInfo", timeout: int = 60
) -> None:
    """Reload code with the provided defs_state_info via gRPC.

    Args:
        api_client: The gRPC client to use
        defs_state_info: The state information to use when reloading code
        timeout: Timeout for the gRPC call in seconds

    Raises:
        DagsterUserCodeProcessError: If the reload operation fails
    """
    from dagster._grpc.client import DagsterGrpcClient

    check.inst_param(api_client, "api_client", DagsterGrpcClient)

    # Serialize the defs_state_info for transmission
    serialized_defs_state_info = serialize_value(defs_state_info)

    # Make the gRPC call
    result = api_client.reload_code_with_state(serialized_defs_state_info, timeout=timeout)

    # Check if there was an error
    if result.serialized_error:
        error_info = deserialize_value(result.serialized_error, SerializableErrorInfo)
        raise DagsterUserCodeProcessError(
            error_info.to_string(), user_code_process_error_infos=[error_info]
        )
