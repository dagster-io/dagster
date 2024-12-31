import asyncio
import json
import uuid
from unittest import mock

import pytest
import responses
from aiohttp import ClientResponseError, hdrs
from aioresponses import aioresponses
from dagster_sigma import SigmaBaseUrl, SigmaOrganization
from dagster_sigma.resource import SigmaFilter, _inode_from_url

from dagster_sigma_tests.utils import get_requests


@responses.activate
def test_authorization(sigma_auth_token: str) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    assert resource.api_token == sigma_auth_token

    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Content-Type"] == "application/x-www-form-urlencoded"
    assert responses.calls[0].request.body == "&".join(
        [
            f"{k}={v}"
            for k, v in {
                "grant_type": "client_credentials",
                "client_id": fake_client_id,
                "client_secret": fake_client_secret,
            }.items()
        ]
    )


@responses.activate
def test_basic_fetch(sigma_auth_token: str, responses: aioresponses) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    responses.add(
        method=hdrs.METH_GET,
        url=f"{SigmaBaseUrl.AWS_US.value}/v2/datasets",
        body=json.dumps({}),
        status=200,
    )

    asyncio.run(resource._fetch_json_async("datasets"))  # noqa: SLF001

    calls = get_requests(responses)
    assert len(calls) == 1
    assert calls[0].headers["Authorization"] == f"Bearer {sigma_auth_token}"


@responses.activate
def test_model_organization_data(sigma_auth_token: str, sigma_sample_data: None) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=None, fetch_column_data=True, fetch_lineage_data=True
        )
    )

    assert len(data.workbooks) == 1
    assert data.workbooks[0].properties["name"] == "Sample Workbook"

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == {_inode_from_url(data.datasets[0].properties["url"])}

    assert data.datasets[0].properties["name"] == "Orders Dataset"
    assert data.datasets[0].columns == {
        "Customer Id",
        "Order Date",
        "Order Id",
        "Modified Date",
        "Status",
    }
    assert data.datasets[0].inputs == {"TESTDB.JAFFLE_SHOP.STG_ORDERS"}


@pytest.mark.parametrize("filter_type", ["workbook_folders", "workbook_names", "both"])
@responses.activate
def test_model_organization_data_filter(
    sigma_auth_token: str, sigma_sample_data: None, filter_type: str
) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    non_matching_filter = (
        {"workbook_folders": [("My Documents", "Test Folder")]}
        if filter_type == "workbook_folders"
        else {"workbooks": [("My Documents", "Test Folder", "Sample Workbook")]}
    )
    matching_filter = (
        {"workbook_folders": [("My Documents", "My Subfolder")]}
        if filter_type == "workbook_folders"
        else {"workbooks": [("My Documents", "My Subfolder", "Sample Workbook")]}
    )

    with mock.patch.object(
        SigmaOrganization,
        "_fetch_pages_for_workbook",
        wraps=resource._fetch_pages_for_workbook,  # noqa: SLF001
    ) as mock_fetch_pages:
        data = asyncio.run(
            resource.build_organization_data(
                sigma_filter=SigmaFilter(**non_matching_filter, include_unused_datasets=True),
                fetch_column_data=True,
                fetch_lineage_data=True,
            )
        )
        assert len(data.workbooks) == 0
        assert len(data.datasets) == 1

        # We don't fetch the workbooks, so we shouldn't have made any calls
        assert len(mock_fetch_pages.mock_calls) == 0

        data = asyncio.run(
            resource.build_organization_data(
                sigma_filter=SigmaFilter(**non_matching_filter, include_unused_datasets=False),
                fetch_column_data=True,
                fetch_lineage_data=True,
            )
        )
        assert len(data.workbooks) == 0
        assert len(data.datasets) == 0

        # We still don't fetch the workbooks, so we shouldn't have made any calls
        assert len(mock_fetch_pages.mock_calls) == 0

        data = asyncio.run(
            resource.build_organization_data(
                sigma_filter=SigmaFilter(**matching_filter, include_unused_datasets=False),
                fetch_column_data=True,
                fetch_lineage_data=True,
            )
        )

        assert len(data.workbooks) == 1
        assert len(data.datasets) == 1
        assert data.workbooks[0].properties["name"] == "Sample Workbook"

        # We fetch the workbook thrice, once for generating the workbook object,
        # once for fetching column data, and once for fetching lineage data
        # (the results are cached, so we don't actually make three calls out to the API)
        assert len(mock_fetch_pages.mock_calls) == 3

        data = asyncio.run(
            resource.build_organization_data(
                sigma_filter=SigmaFilter(
                    workbook_folders=[("My Documents",)], workbooks=[("Does", "Not", "Exist")]
                ),
                fetch_column_data=True,
                fetch_lineage_data=True,
            )
        )

        assert len(data.workbooks) == 1
        assert data.workbooks[0].properties["name"] == "Sample Workbook"


@responses.activate
def test_model_organization_data_skip_fetch_col_data(
    sigma_auth_token: str, sigma_sample_data: None
) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=None, fetch_column_data=False, fetch_lineage_data=True
        )
    )

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == {_inode_from_url(data.datasets[0].properties["url"])}

    assert data.datasets[0].properties["name"] == "Orders Dataset"
    assert data.datasets[0].columns == set()


@responses.activate
def test_model_organization_data_skip_fetch_lineage(
    sigma_auth_token: str, sigma_sample_data: None
) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=None, fetch_column_data=True, fetch_lineage_data=False
        )
    )

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == set()


@responses.activate
def test_model_organization_data_warn_err(
    sigma_auth_token: str, sigma_sample_data: None, lineage_warn: None
) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
        warn_on_lineage_fetch_error=False,
    )

    with pytest.raises(ClientResponseError):
        asyncio.run(
            resource.build_organization_data(
                sigma_filter=None, fetch_column_data=True, fetch_lineage_data=True
            )
        )


@responses.activate
def test_model_organization_data_warn_no_err(
    sigma_auth_token: str, sigma_sample_data: None, lineage_warn: None
) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource_warn = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
        warn_on_lineage_fetch_error=True,
    )

    data = asyncio.run(
        resource_warn.build_organization_data(
            sigma_filter=None, fetch_column_data=True, fetch_lineage_data=True
        )
    )

    assert len(data.workbooks) == 1
    assert data.workbooks[0].properties["name"] == "Sample Workbook"

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == {_inode_from_url(data.datasets[0].properties["url"])}
