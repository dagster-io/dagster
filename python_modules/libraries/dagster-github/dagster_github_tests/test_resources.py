import time

import requests
import responses
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dagster import ModeDefinition, execute_solid, solid
from dagster_github import github_resource
from dagster_github.resources import GithubResource

FAKE_PRIVATE_RSA_KEY = (
    rsa.generate_private_key(public_exponent=65537, key_size=1024, backend=default_backend())
    .private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    .decode("utf-8")
)


@responses.activate
def test_github_resource_get_installations():
    @solid(required_resource_keys={"github"})
    def github_solid(context):
        assert context.resources.github
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                "https://api.github.com/app/installations",
                status=200,
                json={},
            )
            context.resources.github.get_installations()

    result = execute_solid(
        github_solid,
        run_config={
            "resources": {
                "github": {
                    "config": {
                        "github_app_id": 123,
                        "github_app_private_rsa_key": FAKE_PRIVATE_RSA_KEY,
                        "github_installation_id": 123,
                    }
                }
            }
        },
        mode_def=ModeDefinition(resource_defs={"github": github_resource}),
    )
    assert result.success


@responses.activate
def test_github_resource_create_issue():
    @solid(required_resource_keys={"github"})
    def github_solid(context):
        assert context.resources.github
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
            context.resources.github.create_issue(
                repo_name="dagster",
                repo_owner="dagster-io",
                title="test",
                body="body",
            )

    result = execute_solid(
        github_solid,
        run_config={
            "resources": {
                "github": {
                    "config": {
                        "github_app_id": 123,
                        "github_app_private_rsa_key": FAKE_PRIVATE_RSA_KEY,
                        "github_installation_id": 123,
                    }
                }
            }
        },
        mode_def=ModeDefinition(resource_defs={"github": github_resource}),
    )
    assert result.success


@responses.activate
def test_github_resource_execute():
    @solid(required_resource_keys={"github"})
    def github_solid(context):
        assert context.resources.github
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
            context.resources.github.execute(
                query="""
                query get_repo_id($repo_name: String!, $repo_owner: String!) {
                    repository(name: $repo_name, owner: $repo_owner) {
                        id
                    }
                }""",
                variables={"repo_name": "dagster", "repo_owner": "dagster-io"},
            )

    result = execute_solid(
        github_solid,
        run_config={
            "resources": {
                "github": {
                    "config": {
                        "github_app_id": 123,
                        # Do not be alarmed, this is a fake key
                        "github_app_private_rsa_key": FAKE_PRIVATE_RSA_KEY,
                        "github_installation_id": 123,
                    }
                }
            }
        },
        mode_def=ModeDefinition(resource_defs={"github": github_resource}),
    )
    assert result.success


@responses.activate
def test_github_resource_token_expiration():
    class GithubResourceTesting(GithubResource):
        def __init__(self, client, app_id, app_private_rsa_key, default_installation_id):
            GithubResource.__init__(
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

    resource = GithubResourceTesting(
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
