from dagster import check
from dagster.cli.workspace.workspace import IWorkspace
from dagster.core.host_representation.origin import RepositoryLocationOrigin
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation


class DynamicWorkspace(IWorkspace):
    """An IWorkspace that maintains a dynamic list of origins, loading them
    lazily as they are requested.

    Probably move to the workspace module
    """

    def __init__(self, grpc_server_registry):
        from dagster.core.host_representation.grpc_server_registry import GrpcServerRegistry

        self._locations = {}

        self._grpc_server_registry = check.inst_param(
            grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
        )

    def __enter__(self):
        return self

    @property
    def grpc_server_registry(self):
        return self._grpc_server_registry

    def get_location(self, origin):
        check.inst_param(origin, "origin", RepositoryLocationOrigin)
        origin_id = origin.get_id()
        existing_location = self._locations.get(origin_id)

        if not self._grpc_server_registry.supports_origin(origin):
            location = existing_location if existing_location else origin.create_location()
        else:
            endpoint = self._grpc_server_registry.get_grpc_endpoint(origin)

            # Registry may periodically reload the endpoint, at which point the server ID will
            # change and we should reload the location
            if existing_location and existing_location.server_id != endpoint.server_id:
                existing_location.cleanup()
                existing_location = None

            location = (
                existing_location
                if existing_location
                else GrpcServerRepositoryLocation(
                    origin=origin,
                    server_id=endpoint.server_id,
                    port=endpoint.port,
                    socket=endpoint.socket,
                    host=endpoint.host,
                    heartbeat=True,
                    watch_server=False,
                    grpc_server_registry=self._grpc_server_registry,
                )
            )

        self._locations[origin_id] = location
        return self._locations[origin_id]

    def cleanup(self):
        for location in self._locations.values():
            location.cleanup()
        self._locations = {}

    def __exit__(self, exception_type, exception_value, traceback):
        self.cleanup()
