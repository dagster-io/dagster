from dagit.starlette import ROOT_ADDRESS_STATIC_RESOURCES
from starlette.testclient import TestClient


def test_dagit_info(empty_app):
    client = TestClient(empty_app)
    response = client.get("/dagit_info")
    assert response.status_code == 200
    assert response.json() == {
        "dagit_version": "dev",
        "dagster_version": "dev",
        "dagster_graphql_version": "dev",
    }


def test_static_resources(empty_app):
    client = TestClient(empty_app)

    # make sure we did not fallback to the index html
    # for static resources at /
    for address in ROOT_ADDRESS_STATIC_RESOURCES:
        response = client.get(address)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] != "text/html"

    response = client.get("/vendor/graphql-playground/middleware.js")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] != "application/js"
