import time

import pytest
import requests
import responses
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dagster import op
from dagster._utils.test import wrap_op_in_graph_and_execute
from dagster_github.resources import GithubClient, GithubResource

FAKE_PRIVATE_RSA_KEY = (
    rsa.generate_private_key(public_exponent=65537, key_size=1024, backend=default_backend())
    .private_bytes(
        encoding=serialization.Encoding.PEM,  # type: ignore  # (bad stubs)
        format=serialization.PrivateFormat.TraditionalOpenSSL,  # type: ignore  # (bad stubs)
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)


@responses.activate
def test_github_resource_get_installations():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                "https://api.github.com/app/installations",
                status=200,
                json={},
            )
            github.get_installations()

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_get_installations_with_hostname():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                "https://github.contoso.com/api/v3/app/installations",
                status=200,
                json={},
            )
            github.get_installations()

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
                github_hostname="github.contoso.com",
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_create_issue():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://api.github.com/app/installations/123/access_tokens",
                status=201,
                json={
                    "token": "fake_token",
                    "expires_at": "2016-07-11T22:14:10Z",
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {"repository": {"id": 123}},
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={},
            )
            github.create_issue(
                repo_name="dagster",
                repo_owner="dagster-io",
                title="test",
                body="body",
            )

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_create_ref():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://api.github.com/app/installations/123/access_tokens",
                status=201,
                json={
                    "token": "fake_token",
                    "expires_at": "2016-07-11T22:14:10Z",
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {
                        "repository": {"id": 123, "ref": {"target": {"oid": "refs/heads/master"}}}
                    },
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={},
            )
            github.create_ref(
                repo_name="dagster",
                repo_owner="dagster-io",
                source="refs/heads/master",
                target="refs/heads/test-branch",
            )

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_create_pull_request():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://api.github.com/app/installations/123/access_tokens",
                status=201,
                json={
                    "token": "fake_token",
                    "expires_at": "2016-07-11T22:14:10Z",
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {
                        "repository": {"id": 123, "ref": {"target": {"oid": "refs/heads/master"}}}
                    },
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {
                        "repository": {"id": 456, "ref": {"target": {"oid": "refs/heads/master"}}}
                    },
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {
                        "clientMutationId": "1",
                        "pullRequest": {"id": "2", "url": ""},
                    },
                },
            )
            github.create_pull_request(
                base_repo_name="dagster",
                base_repo_owner="dagster-io",
                base_ref_name="refs/heads/master",
                head_repo_name="dagster",
                head_repo_owner="some-user",
                head_ref_name="refs/heads/test-branch",
                title="pr-title",
            )

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_execute():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()
        assert github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://api.github.com/app/installations/123/access_tokens",
                status=201,
                json={
                    "token": "fake_token",
                    "expires_at": "2016-07-11T22:14:10Z",
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={
                    "data": {"repository": {"id": 123}},
                },
            )
            github.execute(
                query="""
                query get_repo_id($repo_name: String!, $repo_owner: String!) {
                    repository(name: $repo_name, owner: $repo_owner) {
                        id
                    }
                }""",
                variables={"repo_name": "dagster", "repo_owner": "dagster-io"},
            )

    result = wrap_op_in_graph_and_execute(
        github_op,
        resources={
            "github_client_resource": GithubResource(
                github_app_id=123,
                github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                github_installation_id=123,
            )
        },
    )
    assert result.success


@responses.activate
def test_github_resource_token_expiration():
    class GithubClientTesting(GithubClient):
        def __init__(self, client, app_id, app_private_rsa_key, default_installation_id):
            GithubClient.__init__(
                self,
                client=client,
                app_id=app_id,
                app_private_rsa_key=app_private_rsa_key,
                default_installation_id=default_installation_id,
            )
            self.installation_tokens = {
                "123": {"value": "test", "expires": int(time.time()) - 1000}
            }
            self.app_token = {
                "value": "test",
                "expires": int(time.time()) - 1000,
            }

    resource = GithubClientTesting(
        client=requests.Session(),
        app_id="abc",
        app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
        default_installation_id="123",
    )
    with responses.RequestsMock() as rsps:
        rsps.add(
            rsps.POST,
            "https://api.github.com/app/installations/123/access_tokens",
            status=201,
            json={
                "token": "fake_token",
                "expires_at": "2016-07-11T22:14:10Z",
            },
        )
        rsps.add(
            rsps.POST,
            "https://api.github.com/graphql",
            status=200,
            json={
                "data": {"repository": {"id": 123}},
            },
        )
        res = resource.execute(
            query="""
            query get_repo_id($repo_name: String!, $repo_owner: String!) {
                repository(name: $repo_name, owner: $repo_owner) {
                    id
                }
            }""",
            variables={"repo_name": "dagster", "repo_owner": "dagster-io"},
        )
        assert res["data"]["repository"]["id"] == 123


def test_github_resource_raises_on_errors():
    @op
    def github_op(github_client_resource: GithubResource):
        github = github_client_resource.get_client()

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "https://api.github.com/app/installations/123/access_tokens",
                status=201,
                json={
                    "token": "fake_token",
                    "expires_at": "2016-07-11T22:14:10Z",
                },
            )
            rsps.add(
                rsps.POST,
                "https://api.github.com/graphql",
                status=200,
                json={"errors": [{"type": "error", "message": "message"}]},
            )
            github.execute("query")

    with pytest.raises(RuntimeError):
        wrap_op_in_graph_and_execute(
            github_op,
            resources={
                "github_client_resource": GithubResource(
                    github_app_id=123,
                    github_app_private_rsa_key=FAKE_PRIVATE_RSA_KEY,
                    github_installation_id=123,
                )
            },
        )
