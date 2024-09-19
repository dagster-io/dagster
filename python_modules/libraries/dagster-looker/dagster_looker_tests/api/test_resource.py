import responses
from dagster_looker.api.resource import LookerResource


@responses.activate(assert_all_requests_are_fired=True)
def test_resource_request() -> None:
    test_base_url = "https://your.cloud.looker.com"
    resource = LookerResource(
        base_url=test_base_url, client_id="client_id", client_secret="client_secret"
    )

    responses.add(method=responses.POST, url=f"{test_base_url}/api/4.0/login", json={})

    resource.get_sdk().login()
