import logging
import uuid
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from dagster import asset, instance_for_test, materialize
from dagster_tableau.resources import TableauCloudWorkspace, TableauServerWorkspace


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_basic_resource_request(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    api_token: str,
    workbook_id: str,
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)

    @asset
    def test_assets():
        with resource.get_client() as client:
            client.get_workbooks()
            client.get_workbook(workbook_id=workbook_id)

    with instance_for_test() as instance:
        materialize(
            [test_assets],
            instance=instance,
            resources={"tableau": resource},
        )

    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    get_workbook.assert_called_with(workbook_id=workbook_id)


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_add_data_quality_warning(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    api_token: str,
    workbook_id: str,
    sign_in: MagicMock,
    get_data_source_by_id: MagicMock,
    build_data_quality_warning_item: MagicMock,
    add_data_quality_warning: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    resource = clazz(**resource_args)

    with resource.get_client() as client:
        client.add_data_quality_warning_to_data_source(data_source_id="fake_datasource_id")

    assert get_data_source_by_id.call_count == 1
    assert build_data_quality_warning_item.call_count == 1
    add_data_quality_warning.assert_called_with(
        item=get_data_source_by_id.return_value,
        warning=build_data_quality_warning_item.return_value,
    )


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    response = resource.get_or_fetch_workspace_data()

    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert response.data_sources_by_id.__len__() == 3
    assert (
        response.data_sources_by_id.get("0f5660c7-2b05-4ff0-90ce-3199226956c6").properties.get(  # type: ignore
            "name"
        )
        == "Superstore Datasource"
    )
    assert (
        response.data_sources_by_id.get("1f5660c7-3b05-5ff0-90ce-4199226956c6").properties.get(  # type: ignore
            "name"
        )
        == "Embedded Superstore Datasource"
    )


def _build_workbook_item(*, wb_id: str, name: str, project_name: str, project_id: str) -> MagicMock:
    """Build a mock workbook list item, mirroring the shape returned by `get_workbooks`."""
    workbook_item = MagicMock()
    type(workbook_item).id = PropertyMock(return_value=wb_id)
    type(workbook_item).name = PropertyMock(return_value=name)
    type(workbook_item).project_name = PropertyMock(return_value=project_name)
    type(workbook_item).project_id = PropertyMock(return_value=project_id)
    return workbook_item


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
@pytest.mark.parametrize(
    "bad_workbook_data",
    [
        # Malformed workbook missing `sheets`/`dashboards` entirely (previously raised KeyError).
        {
            "luid": "bad-workbook-id",
            "name": "Bad Workbook",
            "projectName": "bad_project",
            "projectLuid": "bad_project_id",
        },
        # Workbook whose `sheets`/`dashboards` are null rather than lists.
        {
            "luid": "bad-workbook-id",
            "name": "Bad Workbook",
            "projectName": "bad_project",
            "projectLuid": "bad_project_id",
            "sheets": None,
            "dashboards": None,
        },
        # Genuinely empty workbook with no sheets and no dashboards.
        {
            "luid": "bad-workbook-id",
            "name": "Bad Workbook",
            "projectName": "bad_project",
            "projectLuid": "bad_project_id",
            "sheets": [],
            "dashboards": [],
        },
    ],
    ids=["missing_keys", "null_keys", "empty_lists"],
)
def test_fetch_tableau_workspace_data_skips_empty_or_malformed_workbook(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    bad_workbook_data: dict,
    site_name: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A single empty or malformed workbook must be skipped with a warning rather than
    failing the entire workspace load and bringing down the whole code location.
    """
    from dagster_tableau_tests.conftest import (
        SAMPLE_SECOND_WORKBOOK,
        TEST_SECOND_PROJECT_ID,
        TEST_SECOND_PROJECT_NAME,
        TEST_SECOND_WORKBOOK_ID,
    )

    bad_workbook_id = "bad-workbook-id"

    def get_workbook_by_id(workbook_id):
        if workbook_id == bad_workbook_id:
            return {"data": {"workbooks": [bad_workbook_data]}}
        elif workbook_id == TEST_SECOND_WORKBOOK_ID:
            return {"data": {"workbooks": [SAMPLE_SECOND_WORKBOOK]}}
        return {"data": {"workbooks": []}}

    resource = clazz(
        connected_app_client_id=uuid.uuid4().hex,
        connected_app_secret_id=uuid.uuid4().hex,
        connected_app_secret_value=uuid.uuid4().hex,
        username="fake_username",
        site_name=site_name,
        **{host_key: host_value},
    )

    with (
        patch("dagster_tableau.resources.BaseTableauClient.get_workbooks") as mock_get_workbooks,
        patch("dagster_tableau.resources.BaseTableauClient.get_workbook") as mock_get_workbook,
    ):
        mock_get_workbooks.return_value = [
            _build_workbook_item(
                wb_id=bad_workbook_id,
                name="Bad Workbook",
                project_name="bad_project",
                project_id="bad_project_id",
            ),
            _build_workbook_item(
                wb_id=TEST_SECOND_WORKBOOK_ID,
                name="Second Workbook",
                project_name=TEST_SECOND_PROJECT_NAME,
                project_id=TEST_SECOND_PROJECT_ID,
            ),
        ]
        mock_get_workbook.side_effect = get_workbook_by_id

        with caplog.at_level(logging.WARNING):
            response = resource.fetch_tableau_workspace_data()

    # The bad workbook is skipped, but the valid workbook still loads successfully.
    assert bad_workbook_id not in response.workbooks_by_id
    assert TEST_SECOND_WORKBOOK_ID in response.workbooks_by_id
    assert "Bad Workbook" in caplog.text
    assert "Skipping" in caplog.text


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_skips_workbook_that_raises(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If fetching/parsing a single workbook raises, it is skipped with a warning rather than
    aborting the entire workspace load.
    """
    from dagster_tableau_tests.conftest import (
        SAMPLE_SECOND_WORKBOOK,
        TEST_SECOND_PROJECT_ID,
        TEST_SECOND_PROJECT_NAME,
        TEST_SECOND_WORKBOOK_ID,
    )

    raising_workbook_id = "raising-workbook-id"

    def get_workbook_by_id(workbook_id):
        if workbook_id == raising_workbook_id:
            raise Exception("Tableau API exploded for this workbook")
        elif workbook_id == TEST_SECOND_WORKBOOK_ID:
            return {"data": {"workbooks": [SAMPLE_SECOND_WORKBOOK]}}
        return {"data": {"workbooks": []}}

    resource = clazz(
        connected_app_client_id=uuid.uuid4().hex,
        connected_app_secret_id=uuid.uuid4().hex,
        connected_app_secret_value=uuid.uuid4().hex,
        username="fake_username",
        site_name=site_name,
        **{host_key: host_value},
    )

    with (
        patch("dagster_tableau.resources.BaseTableauClient.get_workbooks") as mock_get_workbooks,
        patch("dagster_tableau.resources.BaseTableauClient.get_workbook") as mock_get_workbook,
    ):
        mock_get_workbooks.return_value = [
            _build_workbook_item(
                wb_id=raising_workbook_id,
                name="Raising Workbook",
                project_name="bad_project",
                project_id="bad_project_id",
            ),
            _build_workbook_item(
                wb_id=TEST_SECOND_WORKBOOK_ID,
                name="Second Workbook",
                project_name=TEST_SECOND_PROJECT_NAME,
                project_id=TEST_SECOND_PROJECT_ID,
            ),
        ]
        mock_get_workbook.side_effect = get_workbook_by_id

        with caplog.at_level(logging.WARNING):
            response = resource.fetch_tableau_workspace_data()

    assert raising_workbook_id not in response.workbooks_by_id
    assert TEST_SECOND_WORKBOOK_ID in response.workbooks_by_id
    assert "Raising Workbook" in caplog.text
    assert "Skipping" in caplog.text


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_workbook_selector_by_id(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data filters workbooks by ID when selector is provided."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    # Import after resource is created to avoid import errors
    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a workbook selector that matches the test workbook ID
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == workbook_id

    response = resource.fetch_tableau_workspace_data(workbook_selector_fn=workbook_selector)

    # Verify that workbooks were filtered
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1  # Should only fetch the matching workbook
    assert len(response.workbooks_by_id) == 1
    assert workbook_id in response.workbooks_by_id


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_workbook_selector_excludes_non_matching_workbooks(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data excludes non-matching workbooks."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a workbook selector that never matches
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == "non-existent-workbook-id"

    response = resource.fetch_tableau_workspace_data(workbook_selector_fn=workbook_selector)

    # Verify that no workbooks were fetched
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 0  # Should not fetch any workbooks
    assert len(response.workbooks_by_id) == 0
    assert len(response.sheets_by_id) == 0
    assert len(response.dashboards_by_id) == 0


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_project_selector_by_id(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data filters by project ID."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a project selector that matches by project ID
    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_id == "test_project_id"

    response = resource.fetch_tableau_workspace_data(project_selector_fn=project_selector)

    # Verify that workbooks were filtered by project
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1  # Should fetch the matching workbook
    assert len(response.workbooks_by_id) == 1


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_project_selector_by_name(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that fetch_tableau_workspace_data filters by project name."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Create a project selector that matches by project name
    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_name == "test_project_name"

    response = resource.fetch_tableau_workspace_data(project_selector_fn=project_selector)

    # Verify that workbooks were filtered by project
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1  # Should fetch the matching workbook
    assert len(response.workbooks_by_id) == 1


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_both_selectors_or_logic(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that both selectors use OR logic - workbook included if it matches either selector."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Workbook selector that never matches
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == "non-existent-workbook-id"

    # Project selector that matches the test workbook's project
    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_id == "test_project_id"

    response = resource.fetch_tableau_workspace_data(
        workbook_selector_fn=workbook_selector, project_selector_fn=project_selector
    )

    # Should fetch the workbook because it matches the project selector (OR logic)
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert len(response.workbooks_by_id) == 1


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_both_selectors_workbook_matches_workbook_selector(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that workbook is included when it matches workbook_selector but not project_selector."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Workbook selector that matches
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == workbook_id

    # Project selector that never matches
    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_id == "non-existent-project-id"

    response = resource.fetch_tableau_workspace_data(
        workbook_selector_fn=workbook_selector, project_selector_fn=project_selector
    )

    # Should fetch the workbook because it matches the workbook selector (OR logic)
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert len(response.workbooks_by_id) == 1


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_both_selectors_neither_matches(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that workbook is excluded when it matches neither selector."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Both selectors never match
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == "non-existent-workbook-id"

    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_id == "non-existent-project-id"

    response = resource.fetch_tableau_workspace_data(
        workbook_selector_fn=workbook_selector, project_selector_fn=project_selector
    )

    # Should not fetch any workbooks because neither selector matches
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 0
    assert len(response.workbooks_by_id) == 0
    assert len(response.sheets_by_id) == 0
    assert len(response.dashboards_by_id) == 0


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_with_both_selectors_both_match(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    workbook_id: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that workbook is included when it matches both selectors."""
    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }
    resource = clazz(**resource_args)

    from dagster_tableau.translator import TableauWorkbookMetadata

    # Both selectors match
    def workbook_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.id == workbook_id

    def project_selector(metadata: TableauWorkbookMetadata) -> bool:
        return metadata.project_id == "test_project_id"

    response = resource.fetch_tableau_workspace_data(
        workbook_selector_fn=workbook_selector, project_selector_fn=project_selector
    )

    # Should fetch the workbook because both selectors match
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert len(response.workbooks_by_id) == 1


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_project_selector_filters_data_sources(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that project selector filters standalone data sources by their project."""
    from unittest.mock import PropertyMock, patch

    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    # Create mock data sources with different projects
    mock_ds_matching = MagicMock()
    type(mock_ds_matching).id = PropertyMock(return_value="ds1")
    type(mock_ds_matching).name = PropertyMock(return_value="Matching DS")
    type(mock_ds_matching).has_extracts = PropertyMock(return_value=False)
    type(mock_ds_matching).project_id = PropertyMock(return_value="matching_project_id")
    type(mock_ds_matching).project_name = PropertyMock(return_value="matching_project")

    mock_ds_non_matching = MagicMock()
    type(mock_ds_non_matching).id = PropertyMock(return_value="ds2")
    type(mock_ds_non_matching).name = PropertyMock(return_value="Non-matching DS")
    type(mock_ds_non_matching).has_extracts = PropertyMock(return_value=False)
    type(mock_ds_non_matching).project_id = PropertyMock(return_value="other_project_id")
    type(mock_ds_non_matching).project_name = PropertyMock(return_value="other_project")

    # Patch BaseTableauClient.get_data_sources to return our custom data sources
    with patch("dagster_tableau.resources.BaseTableauClient.get_data_sources") as mock_get_ds:
        mock_get_ds.return_value = [mock_ds_matching, mock_ds_non_matching]

        resource = clazz(**resource_args)

        from dagster_tableau.translator import TableauWorkbookMetadata

        # Project selector that only matches the first data source's project
        def project_selector(metadata: TableauWorkbookMetadata) -> bool:
            return metadata.project_id == "matching_project_id"

        response = resource.fetch_tableau_workspace_data(project_selector_fn=project_selector)

        # Should filter data sources by project
        # Workbook has test_project_id which doesn't match, so no workbooks
        assert len(response.workbooks_by_id) == 0
        # Should only have the matching data source
        assert len(response.data_sources_by_id) == 1
        assert "ds1" in response.data_sources_by_id


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_project_selector_excludes_non_matching_data_sources(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that data sources from non-matching projects are excluded."""
    from unittest.mock import PropertyMock, patch

    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    # Create mock data source in a different project
    mock_ds = MagicMock()
    type(mock_ds).id = PropertyMock(return_value="ds1")
    type(mock_ds).name = PropertyMock(return_value="Other Project DS")
    type(mock_ds).has_extracts = PropertyMock(return_value=False)
    type(mock_ds).project_id = PropertyMock(return_value="other_project_id")
    type(mock_ds).project_name = PropertyMock(return_value="other_project")

    # Patch BaseTableauClient.get_data_sources to return our custom data source
    with patch("dagster_tableau.resources.BaseTableauClient.get_data_sources") as mock_get_ds:
        mock_get_ds.return_value = [mock_ds]

        resource = clazz(**resource_args)

        from dagster_tableau.translator import TableauWorkbookMetadata

        # Project selector that matches the workbook's project but not the data source's
        def project_selector(metadata: TableauWorkbookMetadata) -> bool:
            return metadata.project_id == "test_project_id"

        response = resource.fetch_tableau_workspace_data(project_selector_fn=project_selector)

        # Should include the workbook (matches project selector)
        assert len(response.workbooks_by_id) == 1
        # Should have embedded data sources from the workbook's sheets (3 total)
        # but NOT the standalone data source we patched in (different project)
        assert len(response.data_sources_by_id) == 3
        # Verify the patched standalone data source is NOT included
        assert "ds1" not in response.data_sources_by_id


@pytest.mark.parametrize(
    "clazz,host_key,host_value",
    [
        (TableauServerWorkspace, "server_name", "fake_server_name"),
        (TableauCloudWorkspace, "pod_name", "fake_pod_name"),
    ],
)
def test_fetch_tableau_workspace_data_project_selector_by_name_filters_data_sources(
    clazz: type[TableauCloudWorkspace] | type[TableauServerWorkspace],
    host_key: str,
    host_value: str,
    site_name: str,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
) -> None:
    """Test that project selector by name filters data sources correctly."""
    from unittest.mock import PropertyMock, patch

    connected_app_client_id = uuid.uuid4().hex
    connected_app_secret_id = uuid.uuid4().hex
    connected_app_secret_value = uuid.uuid4().hex
    username = "fake_username"

    resource_args = {
        "connected_app_client_id": connected_app_client_id,
        "connected_app_secret_id": connected_app_secret_id,
        "connected_app_secret_value": connected_app_secret_value,
        "username": username,
        "site_name": site_name,
        host_key: host_value,
    }

    # Create mock data source with specific project name
    mock_ds = MagicMock()
    type(mock_ds).id = PropertyMock(return_value="ds1")
    type(mock_ds).name = PropertyMock(return_value="My DS")
    type(mock_ds).has_extracts = PropertyMock(return_value=False)
    type(mock_ds).project_id = PropertyMock(return_value="proj1")
    type(mock_ds).project_name = PropertyMock(return_value="Analytics Project")

    # Patch BaseTableauClient.get_data_sources to return our custom data source
    with patch("dagster_tableau.resources.BaseTableauClient.get_data_sources") as mock_get_ds:
        mock_get_ds.return_value = [mock_ds]

        resource = clazz(**resource_args)

        from dagster_tableau.translator import TableauWorkbookMetadata

        # Project selector that matches by project name
        def project_selector(metadata: TableauWorkbookMetadata) -> bool:
            return metadata.project_name == "Analytics Project"

        response = resource.fetch_tableau_workspace_data(project_selector_fn=project_selector)

        # Should include the data source (matches by project name)
        assert len(response.data_sources_by_id) == 1
        assert "ds1" in response.data_sources_by_id
