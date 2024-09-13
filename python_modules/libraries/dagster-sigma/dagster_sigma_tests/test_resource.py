import uuid

import responses
from dagster_sigma import SigmaBaseUrl, SigmaOrganization
from dagster_sigma.resource import _inode_from_url


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
def test_basic_fetch(sigma_auth_token: str) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    responses.add(
        method=responses.GET,
        url=f"{SigmaBaseUrl.AWS_US.value}/v2/datasets",
        json={},
        status=200,
    )

    resource.fetch_json("datasets")

    assert len(responses.calls) == 2
    assert responses.calls[1].request.headers["Authorization"] == f"Bearer {sigma_auth_token}"


@responses.activate
def test_model_organization_data(sigma_auth_token: str, sigma_sample_data: None) -> None:
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex

    resource = SigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US,
        client_id=fake_client_id,
        client_secret=fake_client_secret,
    )

    data = resource.get_organization_data()

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
