import uuid

import responses
from dagster_powerbi import PowerBIWorkspace
from dagster_powerbi.resource import (
    BASE_API_URL,
    MICROSOFT_LOGIN_URL,
    PowerBIServicePrincipal,
    PowerBIToken,
)


@responses.activate
def test_basic_resource_request() -> None:
    fake_token = uuid.uuid4().hex
    fake_workspace_id = uuid.uuid4().hex
    resource = PowerBIWorkspace(
        credentials=PowerBIToken(api_token=fake_token),
        workspace_id=fake_workspace_id,
    )

    responses.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{fake_workspace_id}/reports",
        json={},
        status=200,
    )

    resource._get_reports()  # noqa: SLF001

    assert len(responses.calls) == 1
    assert responses.calls[0].request.headers["Authorization"] == f"Bearer {fake_token}"


@responses.activate
def test_service_principal_auth() -> None:
    fake_token = uuid.uuid4().hex
    fake_workspace_id = uuid.uuid4().hex
    fake_client_id = uuid.uuid4().hex
    fake_client_secret = uuid.uuid4().hex
    fake_tenant_id = uuid.uuid4().hex

    resource = PowerBIWorkspace(
        credentials=PowerBIServicePrincipal(
            client_id=fake_client_id,
            client_secret=fake_client_secret,
            tenant_id=fake_tenant_id,
        ),
        workspace_id=fake_workspace_id,
    )

    responses.add(
        method=responses.POST,
        url=MICROSOFT_LOGIN_URL.format(tenant_id=fake_tenant_id),
        json={"access_token": fake_token, "expires_in": 3600},
        status=200,
    )

    responses.add(
        method=responses.GET,
        url=f"{BASE_API_URL}/groups/{fake_workspace_id}/reports",
        json={},
        status=200,
    )

    resource._get_reports()  # noqa: SLF001

    assert len(responses.calls) == 2
    assert fake_client_id in responses.calls[0].request.body
    assert fake_client_secret in responses.calls[0].request.body
    assert responses.calls[1].request.headers["Authorization"] == f"Bearer {fake_token}"


@responses.activate
def test_service_principal_refreshes_token_five_minutes_early() -> None:
    first_token = uuid.uuid4().hex
    second_token = uuid.uuid4().hex
    fake_workspace_id = uuid.uuid4().hex
    fake_tenant_id = uuid.uuid4().hex

    resource = PowerBIWorkspace(
        credentials=PowerBIServicePrincipal(
            client_id=uuid.uuid4().hex,
            client_secret=uuid.uuid4().hex,
            tenant_id=fake_tenant_id,
        ),
        workspace_id=fake_workspace_id,
    )

    login_url = MICROSOFT_LOGIN_URL.format(tenant_id=fake_tenant_id)
    # Lifetime equals the refresh offset, so the next request treats the token as due.
    responses.add(
        method=responses.POST,
        url=login_url,
        json={"access_token": first_token, "expires_in": 300},
        status=200,
    )
    responses.add(
        method=responses.POST,
        url=login_url,
        json={"access_token": second_token, "expires_in": 3600},
        status=200,
    )

    reports_url = f"{BASE_API_URL}/groups/{fake_workspace_id}/reports"
    responses.add(method=responses.GET, url=reports_url, json={}, status=200)
    responses.add(method=responses.GET, url=reports_url, json={}, status=200)

    resource._fetch("reports")  # noqa: SLF001
    resource._fetch("reports")  # noqa: SLF001

    assert len(responses.calls) == 4
    assert responses.calls[1].request.headers["Authorization"] == f"Bearer {first_token}"
    assert responses.calls[3].request.headers["Authorization"] == f"Bearer {second_token}"
