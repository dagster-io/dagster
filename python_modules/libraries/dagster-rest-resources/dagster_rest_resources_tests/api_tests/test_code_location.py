import json
from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.add_or_update_code_location import (
    AddOrUpdateCodeLocation,
    AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentInvalidLocationError,
    AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentPythonError,
    AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentUnauthorizedError,
    AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentWorkspaceEntry,
)
from dagster_rest_resources.__generated__.delete_code_location import (
    DeleteCodeLocation,
    DeleteCodeLocationDeleteLocationDeleteLocationSuccess,
    DeleteCodeLocationDeleteLocationPythonError,
    DeleteCodeLocationDeleteLocationUnauthorizedError,
)
from dagster_rest_resources.__generated__.enums import RepositoryLocationLoadStatus
from dagster_rest_resources.__generated__.get_location_statuses import (
    GetLocationStatuses,
    GetLocationStatusesLocationStatusesOrErrorPythonError,
    GetLocationStatusesLocationStatusesOrErrorWorkspaceLocationStatusEntries,
    GetLocationStatusesLocationStatusesOrErrorWorkspaceLocationStatusEntriesEntries,
)
from dagster_rest_resources.__generated__.list_code_locations import (
    ListCodeLocations,
    ListCodeLocationsWorkspace,
    ListCodeLocationsWorkspaceWorkspaceEntries,
)
from dagster_rest_resources.api.code_location import (
    DgApiCodeLocationApi,
    DgApiCodeLocationDocument,
    DgApiCodeLocationList,
)
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)


def _make_entry(
    location_name: str,
    image: str | None = None,
    python_file: str | None = None,
    module_name: str | None = None,
    package_name: str | None = None,
    autoload_defs_module_name: str | None = None,
) -> ListCodeLocationsWorkspaceWorkspaceEntries:
    metadata: dict = {}
    if image:
        metadata["image"] = image
    if python_file:
        metadata["python_file"] = python_file
    if module_name:
        metadata["module_name"] = module_name
    if package_name:
        metadata["package_name"] = package_name
    if autoload_defs_module_name:
        metadata["autoload_defs_module_name"] = autoload_defs_module_name
    return ListCodeLocationsWorkspaceWorkspaceEntries(
        locationName=location_name,
        serializedDeploymentMetadata=json.dumps(metadata) if metadata else "{}",
    )


def _make_status_entries(
    statuses: dict[str, RepositoryLocationLoadStatus],
) -> GetLocationStatusesLocationStatusesOrErrorWorkspaceLocationStatusEntries:
    return GetLocationStatusesLocationStatusesOrErrorWorkspaceLocationStatusEntries(
        __typename="WorkspaceLocationStatusEntries",
        entries=[
            GetLocationStatusesLocationStatusesOrErrorWorkspaceLocationStatusEntriesEntries(
                name=name, loadStatus=status
            )
            for name, status in statuses.items()
        ],
    )


class TestListCodeLocations:
    def _make_client(
        self,
        entries: list[ListCodeLocationsWorkspaceWorkspaceEntries],
        statuses: dict[str, RepositoryLocationLoadStatus] | None = None,
    ) -> Mock:
        client = Mock(spec=IGraphQLClient)
        client.list_code_locations.return_value = ListCodeLocations(
            workspace=ListCodeLocationsWorkspace(workspaceEntries=entries)
        )
        client.get_location_statuses.return_value = GetLocationStatuses(
            locationStatusesOrError=_make_status_entries(statuses or {})
        )
        return client

    def test_returns_locations(self):
        client = self._make_client(
            entries=[
                _make_entry(
                    "loc-a",
                    image="test-image",
                    module_name="test-module-name",
                    python_file="test-python-file",
                ),
                _make_entry(
                    "loc-b",
                    package_name="test-package-name",
                    autoload_defs_module_name="test-autoload-defs-module-name",
                ),
                _make_entry("loc-c"),
            ],
            statuses={
                "loc-a": RepositoryLocationLoadStatus.LOADED,
                "loc-b": RepositoryLocationLoadStatus.LOADING,
            },
        )

        result = DgApiCodeLocationApi(_client=client).list_code_locations()

        assert len(result.items) == 3
        assert result.total == 3

        loc_a = result.items[0]
        assert loc_a.location_name == "loc-a"
        assert loc_a.image == "test-image"
        assert loc_a.code_source is not None
        assert loc_a.code_source.python_file == "test-python-file"
        assert loc_a.code_source.module_name == "test-module-name"
        assert loc_a.status == RepositoryLocationLoadStatus.LOADED

        loc_b = result.items[1]
        assert loc_b.location_name == "loc-b"
        assert loc_b.image is None
        assert loc_b.code_source is not None
        assert loc_b.code_source.package_name == "test-package-name"
        assert loc_b.code_source.autoload_defs_module_name == "test-autoload-defs-module-name"
        assert loc_b.status == RepositoryLocationLoadStatus.LOADING

        loc_c = result.items[2]
        assert loc_c.location_name == "loc-c"
        assert loc_c.image is None
        assert loc_c.image is None
        assert loc_c.code_source is None
        assert loc_c.status is None

    def test_returns_empty(self):
        client = self._make_client(entries=[])

        result = DgApiCodeLocationApi(_client=client).list_code_locations()

        assert result == DgApiCodeLocationList(items=[])

    def test_status_error_yields_no_statuses(self):
        client = Mock(spec=IGraphQLClient)
        client.list_code_locations.return_value = ListCodeLocations(
            workspace=ListCodeLocationsWorkspace(
                workspaceEntries=[_make_entry("loc-a", image="test-image")]
            )
        )
        client.get_location_statuses.return_value = GetLocationStatuses(
            locationStatusesOrError=GetLocationStatusesLocationStatusesOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        result = DgApiCodeLocationApi(_client=client).list_code_locations()

        assert result.items[0].status is None

    def test_none_workspace_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_code_locations.return_value = ListCodeLocations(workspace=None)
        client.get_location_statuses.return_value = GetLocationStatuses(
            locationStatusesOrError=_make_status_entries({})
        )

        result = DgApiCodeLocationApi(_client=client).list_code_locations()

        assert result == DgApiCodeLocationList(items=[])


class TestGetCodeLocation:
    def test_returns_matching_location(self):
        client = Mock(spec=IGraphQLClient)
        client.list_code_locations.return_value = ListCodeLocations(
            workspace=ListCodeLocationsWorkspace(
                workspaceEntries=[
                    _make_entry("loc-a"),
                    _make_entry("loc-b"),
                ]
            )
        )
        client.get_location_statuses.return_value = GetLocationStatuses(
            locationStatusesOrError=_make_status_entries({})
        )

        result = DgApiCodeLocationApi(_client=client).get_code_location("loc-a")

        assert result is not None
        assert result.location_name == "loc-a"

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_code_locations.return_value = ListCodeLocations(
            workspace=ListCodeLocationsWorkspace(workspaceEntries=[])
        )
        client.get_location_statuses.return_value = GetLocationStatuses(
            locationStatusesOrError=_make_status_entries({})
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Code location not found"):
            DgApiCodeLocationApi(_client=client).get_code_location("missing")


class TestCreateCodeLocation:
    def test_returns_result(self):
        client = Mock(spec=IGraphQLClient)
        client.add_or_update_code_location.return_value = AddOrUpdateCodeLocation(
            addOrUpdateLocationFromDocument=AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentWorkspaceEntry(
                __typename="WorkspaceEntry", locationName="test-loc"
            )
        )
        result = DgApiCodeLocationApi(_client=client).create_code_location(
            DgApiCodeLocationDocument(location_name="test-loc", image="test-image")
        )

        client.add_or_update_code_location.assert_called_once_with(
            document={"location_name": "test-loc", "image": "test-image"}
        )

        assert result.location_name == "test-loc"

    def test_invalid_location_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_or_update_code_location.return_value = AddOrUpdateCodeLocation(
            addOrUpdateLocationFromDocument=AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentInvalidLocationError(
                __typename="InvalidLocationError", errors=[]
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Invalid code location config"):
            DgApiCodeLocationApi(_client=client).create_code_location(
                DgApiCodeLocationDocument(location_name="test-loc")
            )

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_or_update_code_location.return_value = AddOrUpdateCodeLocation(
            addOrUpdateLocationFromDocument=AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error adding code location"):
            DgApiCodeLocationApi(_client=client).create_code_location(
                DgApiCodeLocationDocument(location_name="test-loc")
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.add_or_update_code_location.return_value = AddOrUpdateCodeLocation(
            addOrUpdateLocationFromDocument=AddOrUpdateCodeLocationAddOrUpdateLocationFromDocumentPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error adding code location"):
            DgApiCodeLocationApi(_client=client).create_code_location(
                DgApiCodeLocationDocument(location_name="test-loc")
            )


class TestDeleteCodeLocation:
    def test_returns_result(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_code_location.return_value = DeleteCodeLocation(
            deleteLocation=DeleteCodeLocationDeleteLocationDeleteLocationSuccess(
                __typename="DeleteLocationSuccess", locationName="test-loc"
            )
        )

        result = DgApiCodeLocationApi(_client=client).delete_code_location("test-loc")

        client.delete_code_location.assert_called_once_with(location_name="test-loc")
        assert result.location_name == "test-loc"

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_code_location.return_value = DeleteCodeLocation(
            deleteLocation=DeleteCodeLocationDeleteLocationUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error deleting code location"):
            DgApiCodeLocationApi(_client=client).delete_code_location("test-loc")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.delete_code_location.return_value = DeleteCodeLocation(
            deleteLocation=DeleteCodeLocationDeleteLocationPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error deleting code location"):
            DgApiCodeLocationApi(_client=client).delete_code_location("test-loc")
