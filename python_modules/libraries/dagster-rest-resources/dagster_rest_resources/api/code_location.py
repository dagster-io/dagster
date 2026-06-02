import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typing_extensions import assert_never

from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.code_location import (
    DgApiAddCodeLocationResult,
    DgApiCodeLocation,
    DgApiCodeLocationDocument,
    DgApiCodeLocationList,
    DgApiCodeSource,
    DgApiDeleteCodeLocationResult,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)

if TYPE_CHECKING:
    from dagster_rest_resources.__generated__.enums import RepositoryLocationLoadStatus


@dataclass(frozen=True)
class DgApiCodeLocationApi:
    _client: IGraphQLClient

    def list_code_locations(self) -> DgApiCodeLocationList:
        workspace_result = self._client.list_code_locations()

        statuses_result = self._client.get_location_statuses()

        statuses: dict[str, RepositoryLocationLoadStatus] = {}
        status_or_error = statuses_result.location_statuses_or_error
        match status_or_error.typename__:
            case "WorkspaceLocationStatusEntries":
                statuses = {e.name: e.load_status for e in status_or_error.entries}  # ty: ignore[unresolved-attribute]
            case "PythonError":
                pass
            case _ as unreachable:
                assert_never(unreachable)

        items: list[DgApiCodeLocation] = []
        if workspace_result.workspace:
            for entry in workspace_result.workspace.workspace_entries:
                image: str | None = None
                code_source: DgApiCodeSource | None = None

                raw_metadata = entry.serialized_deployment_metadata
                if raw_metadata:
                    metadata: dict[str, Any] = json.loads(raw_metadata)
                    image = metadata.get("image")
                    python_file = metadata.get("python_file")
                    module_name = metadata.get("module_name")
                    package_name = metadata.get("package_name")
                    autoload_defs_module_name = metadata.get("autoload_defs_module_name")
                    if any([python_file, module_name, package_name, autoload_defs_module_name]):
                        code_source = DgApiCodeSource(
                            python_file=python_file,
                            module_name=module_name,
                            package_name=package_name,
                            autoload_defs_module_name=autoload_defs_module_name,
                        )

                items.append(
                    DgApiCodeLocation(
                        location_name=entry.location_name,
                        image=image,
                        code_source=code_source,
                        status=statuses.get(entry.location_name),
                    )
                )

        return DgApiCodeLocationList(items=items)

    def get_code_location(self, code_location_name: str) -> DgApiCodeLocation:
        location_list = self.list_code_locations()
        for location in location_list.items:
            if location.location_name == code_location_name:
                return location

        raise DagsterPlusGraphqlError(f"Code location not found: {code_location_name}")

    def create_code_location(
        self, document: DgApiCodeLocationDocument
    ) -> DgApiAddCodeLocationResult:
        result = self._client.add_or_update_code_location(
            document=document.to_document_dict()
        ).add_or_update_location_from_document

        match result.typename__:
            case "WorkspaceEntry":
                return DgApiAddCodeLocationResult(location_name=result.location_name)  # ty: ignore[unresolved-attribute]
            case "InvalidLocationError":
                errors = [e for e in result.errors if e is not None]  # ty: ignore[unresolved-attribute]
                raise DagsterPlusGraphqlError("Invalid code location config:\n" + "\n".join(errors))
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error adding code location: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error adding code location: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def delete_code_location(self, location_name: str) -> DgApiDeleteCodeLocationResult:
        result = self._client.delete_code_location(location_name=location_name).delete_location

        match result.typename__:
            case "DeleteLocationSuccess":
                return DgApiDeleteCodeLocationResult(location_name=result.location_name)  # ty: ignore[unresolved-attribute]
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error deleting code location: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error deleting code location: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
