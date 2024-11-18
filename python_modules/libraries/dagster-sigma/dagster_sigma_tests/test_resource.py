import asyncio
import json
import uuid

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

    data = asyncio.run(resource.build_organization_data(sigma_filter=None, fetch_column_data=True))

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


@responses.activate
def test_model_organization_data_filter(sigma_auth_token: str, sigma_sample_data: None) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=SigmaFilter(workbook_folders=[("My Documents", "Test Folder")]),
            fetch_column_data=True,
        )
    )
    assert len(data.workbooks) == 0
    assert len(data.datasets) == 1
    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=SigmaFilter(
                workbook_folders=[("My Documents", "Test Folder")], include_unused_datasets=False
            ),
            fetch_column_data=True,
        )
    )
    assert len(data.workbooks) == 0
    assert len(data.datasets) == 0

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=SigmaFilter(
                workbook_folders=[("My Documents", "My Subfolder")], include_unused_datasets=False
            ),
            fetch_column_data=True,
        )
    )

    assert len(data.workbooks) == 1
    assert len(data.datasets) == 1
    assert data.workbooks[0].properties["name"] == "Sample Workbook"

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=SigmaFilter(workbook_folders=[("My Documents",)]),
            fetch_column_data=True,
        )
    )

    assert len(data.workbooks) == 1
    assert data.workbooks[0].properties["name"] == "Sample Workbook"


@responses.activate
def test_model_organization_data_skip_fetch(sigma_auth_token: str, sigma_sample_data: None) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = asyncio.run(
        resource.build_organization_data(
            sigma_filter=None,
            fetch_column_data=False,
        )
    )

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == {_inode_from_url(data.datasets[0].properties["url"])}

    assert data.datasets[0].properties["name"] == "Orders Dataset"
    assert data.datasets[0].columns == set()


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
        asyncio.run(resource.build_organization_data(sigma_filter=None, fetch_column_data=True))


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
        resource_warn.build_organization_data(sigma_filter=None, fetch_column_data=True)
    )

    assert len(data.workbooks) == 1
    assert data.workbooks[0].properties["name"] == "Sample Workbook"

    assert len(data.datasets) == 1
    assert data.workbooks[0].datasets == {_inode_from_url(data.datasets[0].properties["url"])}
