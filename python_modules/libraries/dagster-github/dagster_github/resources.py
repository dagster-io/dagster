import time
from datetime import datetime

import jwt
import requests
from dagster import Field, IntSource, StringSource, resource


def to_seconds(dt):
    return (dt - datetime(1970, 1, 1)).total_seconds()


class GithubResource:
    def __init__(self, client, app_id, app_private_rsa_key, default_installation_id):
        self.client = client
        self.app_private_rsa_key = app_private_rsa_key
        self.app_id = app_id
        self.default_installation_id = default_installation_id
        self.installation_tokens = {}
        self.app_token = {}

    def __set_app_token(self):
        # from https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/
        # needing to self-sign a JWT
        now = int(time.time())
        # JWT expiration time (10 minute maximum)
        expires = now + (10 * 60)
        encoded_token = jwt.encode(
            {
                # issued at time
                "iat": now,
                # JWT expiration time
                "exp": expires,
                # GitHub App's identifier
                "iss": self.app_id,
            },
            self.app_private_rsa_key,
            algorithm="RS256",
        )
        self.app_token = {
            "value": encoded_token,
            "expires": expires,
        }

    def __check_app_token(self):
        if ("expires" not in self.app_token) or (
            self.app_token["expires"] < (int(time.time()) + 60)
        ):
            self.__set_app_token()

    def get_installations(self, headers=None):
        if headers is None:
            headers = {}
        self.__check_app_token()
        headers["Authorization"] = "Bearer {}".format(self.app_token["value"])
        headers["Accept"] = "application/vnd.github.machine-man-preview+json"
        request = self.client.get(
            "https://api.github.com/app/installations",
            headers=headers,
        )
        request.raise_for_status()
        return request.json()

    def __set_installation_token(self, installation_id, headers=None):
        if headers is None:
            headers = {}
        self.__check_app_token()
        headers["Authorization"] = "Bearer {}".format(self.app_token["value"])
        headers["Accept"] = "application/vnd.github.machine-man-preview+json"
        request = requests.post(
            "https://api.github.com/app/installations/{}/access_tokens".format(installation_id),
            headers=headers,
        )
        request.raise_for_status()
        auth = request.json()
        self.installation_tokens[installation_id] = {
            "value": auth["token"],
            "expires": to_seconds(datetime.strptime(auth["expires_at"], "%Y-%m-%dT%H:%M:%SZ")),
        }

    def __check_installation_tokens(self, installation_id):
        if (installation_id not in self.installation_tokens) or (
            self.installation_tokens[installation_id]["expires"] < (int(time.time()) + 60)
        ):
            self.__set_installation_token(installation_id)

    def execute(self, query, variables, headers=None, installation_id=None):
        if headers is None:
            headers = {}
        if installation_id is None:
            installation_id = self.default_installation_id
        self.__check_installation_tokens(installation_id)
        headers["Authorization"] = "token {}".format(
            self.installation_tokens[installation_id]["value"]
        )
        request = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
        )
        request.raise_for_status()
        return request.json()

    def create_issue(self, repo_name, repo_owner, title, body, installation_id=None):
        if installation_id is None:
            installation_id = self.default_installation_id
        res = self.execute(
            query="""
            query get_repo_id($repo_name: String!, $repo_owner: String!) {
                repository(name: $repo_name, owner: $repo_owner) {
                    id
                }
            }
            """,
            variables={"repo_name": repo_name, "repo_owner": repo_owner},
            installation_id=installation_id,
        )

        return self.execute(
            query="""
                mutation CreateIssue($id: ID!, $title: String!, $body: String!) {
                createIssue(input: {
                    repositoryId: $id,
                    title: $title,
                    body: $body
                }) {
                    clientMutationId,
                    issue {
                        body
                        title
                        url
                    }
                }
                }
            """,
            variables={
                "id": res["data"]["repository"]["id"],
                "title": title,
                "body": body,
            },
            installation_id=installation_id,
        )


@resource(
    config_schema={
        "github_app_id": Field(
            IntSource,
            description="Github Application ID, for more info see https://developer.github.com/apps/",
        ),
        "github_app_private_rsa_key": Field(
            StringSource,
            description="Github Application Private RSA key text, for more info see https://developer.github.com/apps/",
        ),
        "github_installation_id": Field(
            IntSource,
            is_required=False,
            description="Github Application Installation ID, for more info see https://developer.github.com/apps/",
        ),
    },
    description="This resource is for connecting to Github",
)
def github_resource(context):
    return GithubResource(
        client=requests.Session(),
        app_id=context.resource_config["github_app_id"],
        app_private_rsa_key=context.resource_config["github_app_private_rsa_key"],
        default_installation_id=context.resource_config["github_installation_id"],
    )
