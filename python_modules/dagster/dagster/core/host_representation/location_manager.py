from dagster import check

from .origin import RepositoryLocationOrigin
from .repository_location import GrpcServerRepositoryLocation


class RepositoryLocationManager:
    """
    Holds repository locations for reuse
    """

    def __init__(self, grpc_server_registry):
        from dagster.core.host_representation.grpc_server_registry import GrpcServerRegistry

        self._locations = {}

        self._grpc_server_registry = check.inst_param(
            grpc_server_registry, "grpc_server_registry", GrpcServerRegistry
        )

    def __enter__(self):
        return self

    def get_location(self, repository_location_origin):
        check.inst_param(
            repository_location_origin, "repository_location_origin", RepositoryLocationOrigin
        )
        origin_id = repository_location_origin.get_id()
        existing_location = self._locations.get(origin_id)

        if not self._grpc_server_registry.supports_origin(repository_location_origin):
            location = (
                existing_location
                if existing_location
                else repository_location_origin.create_location()
            )
        else:
            endpoint = self._grpc_server_registry.get_grpc_endpoint(repository_location_origin)

            # Registry may periodically reload the endpoint, at which point the server ID will
            # change and we should reload the location
            if existing_location and existing_location.server_id != endpoint.server_id:
                existing_location.cleanup()
                existing_location = None

            location = (
                existing_location
                if existing_location
                else GrpcServerRepositoryLocation(
                    origin=repository_location_origin,
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

    def __exit__(self, exception_type, exception_value, traceback):
        self.cleanup()
