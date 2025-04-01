import pytest
from dagster._cli.workspace.cli_target import WorkspaceOpts
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster_webserver import app
from starlette.testclient import TestClient

SMOKE_TEST_QUERY = """
{
    repositoriesOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryConnection {
            nodes {
                pipelines {
                    name
                }
            }
        }
    }
}
"""


@pytest.mark.parametrize(
    "gen_instance",
    [instance_for_test],
)
def test_smoke_app(gen_instance):
    with gen_instance() as instance:
        with WorkspaceProcessContext(
            instance,
            version="",
            read_only=False,
            workspace_load_target=WorkspaceOpts(
                module_name=("dagster_webserver_tests.toy.bar_repo",)
            ).to_load_target(),
        ) as workspace_process_context:
            asgi_app = app.create_app_from_workspace_process_context(workspace_process_context)
            client = TestClient(asgi_app)

            result = client.post(
                "/graphql",
                json={"query": SMOKE_TEST_QUERY},
            )
            assert result.status_code == 200, result.content
            data = result.json()
            assert len(data["data"]["repositoriesOrError"]["nodes"]) == 1
            assert len(data["data"]["repositoriesOrError"]["nodes"][0]["pipelines"]) == 2
            assert {
                node_data["name"]
                for node_data in data["data"]["repositoriesOrError"]["nodes"][0]["pipelines"]
            } == set(["foo", "baz"])

            result = client.get("/graphql")
            assert result.status_code == 400
            assert result.content == b"No GraphQL query found in the request"

            result = client.get("/notebook?path=foo.bar&repoLocName=foo_repo")
            assert result.status_code == 400
            assert result.content.decode("utf-8") == "Invalid Path"

            result = client.post("/graphql", json={"query": "query { version { slkjd } }"})
            data = result.json()
            assert "errors" in data
            assert len(data["errors"]) == 1
            assert "must not have a selection" in data["errors"][0]["message"]

            # Missing routes redirect to the index.html file of the Dagster UI react app, so the user
            # gets our UI when they navigate to "synthetic" react router URLs.
            result = client.get("foo/bar")
            assert result.status_code == 200, result.content

            result = client.get("pipelines/foo")
            assert result.status_code == 200, result.content
