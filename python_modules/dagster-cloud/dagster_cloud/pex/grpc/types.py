from typing import NamedTuple

import dagster._check as check
from dagster._core.instance.ref import InstanceRef
from dagster._serdes import create_snapshot_id, whitelist_for_serdes
from dagster_cloud_cli.core.workspace import CodeLocationDeployData


# Enough to uniquely create (and later identify) a given PEX server - the
# timestamp is what allows us to reload a location without changing its PEX and
# still create a new server process.
@whitelist_for_serdes
class PexServerHandle(
    NamedTuple(
        "_PexServerHandle",
        [
            ("deployment_name", str),
            ("location_name", str),
            ("metadata_update_timestamp", int),
        ],
    )
):
    def __new__(cls, deployment_name: str, location_name: str, metadata_update_timestamp: int):
        return super().__new__(
            cls,
            check.str_param(deployment_name, "deployment_name"),
            check.str_param(location_name, "location_name"),
            check.int_param(metadata_update_timestamp, "metadata_update_timestamp"),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)


@whitelist_for_serdes(storage_field_names={"code_location_deploy_data": "code_deployment_metadata"})
class CreatePexServerArgs(
    NamedTuple(
        "_CreatePexServerArgs",
        [
            ("server_handle", PexServerHandle),
            ("code_location_deploy_data", CodeLocationDeployData),
            ("instance_ref", InstanceRef | None),
        ],
    )
):
    def __new__(
        cls,
        server_handle: PexServerHandle,
        code_location_deploy_data: CodeLocationDeployData,
        instance_ref: InstanceRef | None = None,
    ):
        return super().__new__(
            cls,
            check.inst_param(server_handle, "server_handle", PexServerHandle),
            check.inst_param(
                code_location_deploy_data, "code_location_deploy_data", CodeLocationDeployData
            ),
            check.opt_inst_param(instance_ref, "instance_ref", InstanceRef),
        )


@whitelist_for_serdes
class CreatePexServerResponse(
    NamedTuple(
        "_CreatePexServerResponse",
        [],
    )
):
    pass


@whitelist_for_serdes
class GetPexServersArgs(
    NamedTuple(
        "_GetPexServersArgs",
        [
            ("deployment_name", str),
            ("location_name", str),
        ],
    )
):
    pass


@whitelist_for_serdes
class GetCrashedPexServersArgs(
    NamedTuple(
        "_GetCrashedPexServersArgs",
        [
            ("deployment_name", str),
            ("location_name", str),
        ],
    )
):
    pass


@whitelist_for_serdes
class GetPexServersResponse(
    NamedTuple(
        "_GetPexServersResponse",
        [
            ("server_handles", list[PexServerHandle]),
        ],
    )
):
    pass


@whitelist_for_serdes
class GetCrashedPexServersResponse(
    NamedTuple(
        "_GetCrashedPexServersResponse",
        [
            ("server_handles", list[PexServerHandle]),
        ],
    )
):
    pass


@whitelist_for_serdes
class ShutdownPexServerArgs(
    NamedTuple(
        "_ShutdownPexServerArgs",
        [
            ("server_handle", PexServerHandle),
        ],
    )
):
    pass


@whitelist_for_serdes
class ShutdownPexServerResponse(
    NamedTuple(
        "_ShutdownPexServerResponse",
        [],
    )
):
    pass
