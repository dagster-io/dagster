from dagit.starlette import create_app
from starlette.testclient import TestClient


def test_dagit_info():
    client = TestClient(create_app())
    response = client.get("/dagit_info")
    assert response.status_code == 200
    assert response.json() == {
        "dagit_version": "dev",
        "dagster_version": "dev",
        "dagster_graphql_version": "dev",
    }
