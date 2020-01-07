import time
from dagster import resource, Field, String, Int
from tenacity import retry, wait_random_exponential, stop_after_delay
import requests
import jwt
import pem


class GithubResource:
    def __init__(self, client, app_id, app_private_rsa_key, default_app_installation_id):
        self.client = client
        self.app_private_rsa_key = app_private_rsa_key
        self.app_id = app_id
        self.default_app_installation_id = default_app_installation_id
        self.set_app_headers()

    def set_app_headers(self):
        # from https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/
        # needing to self-sign a JWT
        now = int(time.time())
        certs = pem.parse(str.encode(self.app_private_rsa_key))
        if len(certs) == 0:
            raise Exception("Invalid app_private_rsa_key")
        encoded_token = jwt.encode(
            {
                # issued at time
                "iat": now,
                # JWT expiration time (10 minute maximum)
                "exp": now + (10 * 60),
                # GitHub App's identifier
                "iss": self.app_id,
            },
            str(certs[0]),
            algorithm="RS256",
        ).decode("utf-8")
        self.app_headers = {
            "Authorization": f"Bearer {encoded_token}",
            "Accept": "application/vnd.github.machine-man-preview+json",
        }

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(100),
        reraise=True,
    )
    def get_installations(self):
        request = self.client.get(
            "https://api.github.com/app/installations", headers=self.app_headers,
        )
        if request.status_code == 200:
            return request.json()
        elif request.status_code == 401:
            self.set_app_headers()
            raise Exception(
                "Request failed and returned code of {}. {}".format(
                    request.status_code, request.json()
                )
            )
        else:
            raise Exception(
                "Request failed and returned code of {}, {}".format(
                    request.status_code, request.json()
                )
            )

    def get_app_installation_headers(self, app_installation_id):
        auth = self.authenticate_as_installation(app_installation_id)
        return {"Authorization": f"token {auth['token']}"}

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(100),
        reraise=True,
    )
    def authenticate_as_installation(self, installation_id):
        request = requests.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=self.app_headers,
        )
        if request.status_code == 201:
            return request.json()
        elif request.status_code == 401:
            self.set_app_headers()
            raise Exception(
                "Request failed and returned code of {}. {}".format(
                    request.status_code, request.json()
                )
            )
        else:
            raise Exception(
                "Request failed and returned code of {}, {}".format(
                    request.status_code, request.json()
                )
            )

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(100),
        reraise=True,
    )
    def execute(self, query, variables, app_installation_id=None):
        if app_installation_id is None:
            app_installation_id = self.default_app_installation_id
        request = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=self.get_app_installation_headers(app_installation_id),
        )
        if request.status_code == 200:
            return request.json()
        elif request.status_code == 401:
            self.set_app_headers()
            raise Exception(
                "Query failed to run by returning code of {}. {}".format(
                    request.status_code, query
                )
            )
        else:
            raise Exception(
                "Query failed to run by returning code of {}. {}".format(
                    request.status_code, query
                )
            )

    def create_issue(self, repo_name, repo_owner, title, body, app_installation_id=None):
        res = self.execute(
            query="""
            query get_repo_id($repo_name: String!, $repo_owner: String!) {
                repository(name: $repo_name, owner: $repo_owner) {
                    id
                }
            }
            """,
            variables={"repo_name": repo_name, "repo_owner": repo_owner},
            app_installation_id=app_installation_id
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
            app_installation_id=app_installation_id
        )

@resource(
    config={
        "github_app_id": Field(
            Int,
            description="Github Application ID, for more info see https://developer.github.com/apps/",
        ),
        "github_app_private_rsa_key": Field(
            String,
            description="Github Application Private RSA key text, for more info see https://developer.github.com/apps/",
        ),
        "default_github_app_installation_id": Field(
            Int,
            is_optional=True,
            description="Default Github Application Installation ID, for more info see https://developer.github.com/apps/",
        )
    },
    description='This resource is for connecting to Github',
)
def github_resource(context):
    return GithubResource(
        client=requests.Session(),
        app_id=context.resource_config["github_app_id"],
        app_private_rsa_key=context.resource_config["github_app_private_rsa_key"],
        default_app_installation_id=context.resource_config["default_github_app_installation_id"],
    )