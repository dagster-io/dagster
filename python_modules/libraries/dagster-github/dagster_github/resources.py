import time
from datetime import datetime
from typing import Any, Optional

import jwt
import requests
from dagster import ConfigurableResource, resource
from dagster._annotations import deprecated, public
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from pydantic import Field

GET_REPO_ID_QUERY = """
query get_repo_id($repo_name: String!, $repo_owner: String!) {
  repository(name: $repo_name, owner: $repo_owner) {
    id
  }
}
"""

GET_REPO_AND_REF_QUERY = """
query get_repo_and_ref($repo_name: String!, $repo_owner: String!, $source: String!) {
  repository(name: $repo_name, owner: $repo_owner) {
    id
    ref(qualifiedName: $source) {
      target {
        oid
      }
    }
  }
}
"""

CREATE_ISSUE_MUTATION = """
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
"""

CREATE_REF_MUTATION = """
mutation CreateRef($id: ID!, $name: String!, $oid: GitObjectID!) {
  createRef(input: {
    repositoryId: $id,
    name: $name,
    oid: $oid
  }) {
    clientMutationId,
    ref {
      id
      name
      target {
        oid
      }
    }
  }
}
"""

CREATE_PULL_REQUEST_MUTATION = """
mutation CreatePullRequest(
  $base_repo_id: ID!,
  $base_ref_name: String!,
  $head_repo_id: ID!,
  $head_ref_name: String!,
  $title: String!,
  $body: String,
  $maintainer_can_modify: Boolean,
  $draft: Boolean
) {
  createPullRequest(input: {
    repositoryId: $base_repo_id,
    baseRefName: $base_ref_name,
    headRepositoryId: $head_repo_id,
    headRefName: $head_ref_name,
    title: $title,
    body: $body,
    maintainerCanModify: $maintainer_can_modify,
    draft: $draft
  }) {
    clientMutationId
    pullRequest {
      id
      url
    }
  }
}
"""


def to_seconds(dt: datetime) -> float:
    return (dt - datetime(1970, 1, 1)).total_seconds()


@deprecated(
    breaking_version="0.27",
    additional_warn_text=(
        "`GithubClient` is deprecated. Use your own resource and client instead. "
        "Learn how to create your own resource here: "
        "https://docs.dagster.io/guides/build/external-resources/defining-resources"
    ),
)
class GithubClient:
    """A client for interacting with the GitHub API.

    This client handles authentication and provides methods for making requests
    to the GitHub API using an authenticated session.

    Args:
        client (requests.Session): The HTTP session used for making requests.
        app_id (int): The GitHub App ID.
        app_private_rsa_key (str): The private RSA key for the GitHub App.
        default_installation_id (Optional[int]): The default installation ID for the GitHub App.
        hostname (Optional[str]): The GitHub hostname, defaults to None.
        installation_tokens (Dict[Any, Any]): A dictionary to store installation tokens.
        app_token (Dict[str, Any]): A dictionary to store the app token.
    """

    def __init__(
        self,
        client: requests.Session,
        app_id: int,
        app_private_rsa_key: str,
        default_installation_id: Optional[int],
        hostname: Optional[str] = None,
    ) -> None:
        self.client = client
        self.app_private_rsa_key = app_private_rsa_key
        self.app_id = app_id
        self.default_installation_id = default_installation_id
        self.installation_tokens: dict[Any, Any] = {}
        self.app_token: dict[str, Any] = {}
        self.hostname = hostname

    def __set_app_token(self) -> None:
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

    def __check_app_token(self) -> None:
        if ("expires" not in self.app_token) or (
            self.app_token["expires"] < (int(time.time()) + 60)
        ):
            self.__set_app_token()

    @public
    def get_installations(self, headers: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Retrieve the list of installations for the authenticated GitHub App.

        This method makes a GET request to the GitHub API to fetch the installations
        associated with the authenticated GitHub App. It ensures that the app token
        is valid and includes it in the request headers.

        Args:
            headers (Optional[Dict[str, Any]]): Optional headers to include in the request.

        Returns:
            Dict[str, Any]: A dictionary containing the installations data.

        Raises:
            requests.exceptions.HTTPError: If the request to the GitHub API fails.
        """
        if headers is None:
            headers = {}
        self.__check_app_token()
        headers["Authorization"] = f"Bearer {self.app_token['value']}"
        headers["Accept"] = "application/vnd.github.machine-man-preview+json"
        request = self.client.get(
            (
                "https://api.github.com/app/installations"
                if self.hostname is None
                else f"https://{self.hostname}/api/v3/app/installations"
            ),
            headers=headers,
        )
        request.raise_for_status()
        return request.json()

    def __set_installation_token(
        self, installation_id: int, headers: Optional[dict[str, Any]] = None
    ) -> None:
        if headers is None:
            headers = {}
        self.__check_app_token()
        headers["Authorization"] = f"Bearer {self.app_token['value']}"
        headers["Accept"] = "application/vnd.github.machine-man-preview+json"
        request = requests.post(
            (
                f"https://api.github.com/app/installations/{installation_id}/access_tokens"
                if self.hostname is None
                else f"https://{self.hostname}/api/v3/app/installations/{installation_id}/access_tokens"
            ),
            headers=headers,
        )
        request.raise_for_status()
        auth = request.json()
        self.installation_tokens[installation_id] = {
            "value": auth["token"],
            "expires": to_seconds(datetime.strptime(auth["expires_at"], "%Y-%m-%dT%H:%M:%SZ")),
        }

    def __check_installation_tokens(self, installation_id: int) -> None:
        if (installation_id not in self.installation_tokens) or (
            self.installation_tokens[installation_id]["expires"] < (int(time.time()) + 60)
        ):
            self.__set_installation_token(installation_id)

    @public
    def execute(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        installation_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the GitHub API.

        This method sends a POST request to the GitHub API with the provided GraphQL query
        and optional variables. It ensures that the appropriate installation token is included
        in the request headers.

        Args:
            query (str): The GraphQL query string to be executed.
            variables (Optional[Dict[str, Any]]): Optional variables to include in the query.
            headers (Optional[Dict[str, Any]]): Optional headers to include in the request.
            installation_id (Optional[int]): The installation ID to use for authentication.

        Returns:
            Dict[str, Any]: The response data from the GitHub API.

        Raises:
            RuntimeError: If no installation ID is provided and no default installation ID is set.
            requests.exceptions.HTTPError: If the request to the GitHub API fails.
        """
        if headers is None:
            headers = {}
        if installation_id is None:
            if self.default_installation_id:
                installation_id = self.default_installation_id
            else:
                raise RuntimeError("No installation_id provided")

        self.__check_installation_tokens(installation_id)
        headers["Authorization"] = f"token {self.installation_tokens[installation_id]['value']}"

        json: dict[str, Any] = {"query": query}
        if variables:
            json["variables"] = variables

        request = requests.post(
            (
                "https://api.github.com/graphql"
                if self.hostname is None
                else f"https://{self.hostname}/api/graphql"
            ),
            json=json,
            headers=headers,
        )
        request.raise_for_status()
        if "errors" in request.json():
            raise RuntimeError(request.json()["errors"])
        return request.json()

    @public
    def create_issue(
        self,
        repo_name: str,
        repo_owner: str,
        title: str,
        body: str,
        installation_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a new issue in the specified GitHub repository.

        This method first retrieves the repository ID using the provided repository name
        and owner, then creates a new issue in that repository with the given title and body.

        Args:
            repo_name (str): The name of the repository where the issue will be created.
            repo_owner (str): The owner of the repository where the issue will be created.
            title (str): The title of the issue.
            body (str): The body content of the issue.
            installation_id (Optional[int]): The installation ID to use for authentication.

        Returns:
            Dict[str, Any]: The response data from the GitHub API containing the created issue details.

        Raises:
            RuntimeError: If there are errors in the response from the GitHub API.
        """
        res = self.execute(
            query=GET_REPO_ID_QUERY,
            variables={"repo_name": repo_name, "repo_owner": repo_owner},
            installation_id=installation_id,
        )

        return self.execute(
            query=CREATE_ISSUE_MUTATION,
            variables={
                "id": res["data"]["repository"]["id"],
                "title": title,
                "body": body,
            },
            installation_id=installation_id,
        )

    @public
    def create_ref(
        self,
        repo_name: str,
        repo_owner: str,
        source: str,
        target: str,
        installation_id=None,
    ) -> dict[str, Any]:
        """Create a new reference (branch) in the specified GitHub repository.

        This method first retrieves the repository ID and the source reference (branch or tag)
        using the provided repository name, owner, and source reference. It then creates a new
        reference (branch) in that repository with the given target name.

        Args:
            repo_name (str): The name of the repository where the reference will be created.
            repo_owner (str): The owner of the repository where the reference will be created.
            source (str): The source reference (branch or tag) from which the new reference will be created.
            target (str): The name of the new reference (branch) to be created.
            installation_id (Optional[int]): The installation ID to use for authentication.

        Returns:
            Dict[str, Any]: The response data from the GitHub API containing the created reference details.

        Raises:
            RuntimeError: If there are errors in the response from the GitHub API.
        """
        res = self.execute(
            query=GET_REPO_AND_REF_QUERY,
            variables={
                "repo_name": repo_name,
                "repo_owner": repo_owner,
                "source": source,
            },
            installation_id=installation_id,
        )

        branch = self.execute(
            query=CREATE_REF_MUTATION,
            variables={
                "id": res["data"]["repository"]["id"],
                "name": target,
                "oid": res["data"]["repository"]["ref"]["target"]["oid"],
            },
            installation_id=installation_id,
        )
        return branch

    @public
    def create_pull_request(
        self,
        base_repo_name: str,
        base_repo_owner: str,
        base_ref_name: str,
        head_repo_name: str,
        head_repo_owner: str,
        head_ref_name: str,
        title: str,
        body: Optional[str] = None,
        maintainer_can_modify: Optional[bool] = None,
        draft: Optional[bool] = None,
        installation_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a new pull request in the specified GitHub repository.

        This method creates a pull request from the head reference (branch) to the base reference (branch)
        in the specified repositories. It uses the provided title and body for the pull request description.

        Args:
            base_repo_name (str): The name of the base repository where the pull request will be created.
            base_repo_owner (str): The owner of the base repository.
            base_ref_name (str): The name of the base reference (branch) to which the changes will be merged.
            head_repo_name (str): The name of the head repository from which the changes will be taken.
            head_repo_owner (str): The owner of the head repository.
            head_ref_name (str): The name of the head reference (branch) from which the changes will be taken.
            title (str): The title of the pull request.
            body (Optional[str]): The body content of the pull request. Defaults to None.
            maintainer_can_modify (Optional[bool]): Whether maintainers can modify the pull request. Defaults to None.
            draft (Optional[bool]): Whether the pull request is a draft. Defaults to None.
            installation_id (Optional[int]): The installation ID to use for authentication.

        Returns:
            Dict[str, Any]: The response data from the GitHub API containing the created pull request details.

        Raises:
            RuntimeError: If there are errors in the response from the GitHub API.
        """
        base = self.execute(
            query=GET_REPO_ID_QUERY,
            variables={"repo_name": base_repo_name, "repo_owner": base_repo_owner},
            installation_id=installation_id,
        )
        head = self.execute(
            query=GET_REPO_ID_QUERY,
            variables={"repo_name": head_repo_name, "repo_owner": head_repo_owner},
            installation_id=installation_id,
        )
        pull_request = self.execute(
            query=CREATE_PULL_REQUEST_MUTATION,
            variables={
                "base_repo_id": base["data"]["repository"]["id"],
                "base_ref_name": base_ref_name,
                "head_repo_id": head["data"]["repository"]["id"],
                "head_ref_name": head_ref_name,
                "title": title,
                "body": body,
                "maintainer_can_modify": maintainer_can_modify,
                "draft": draft,
            },
            installation_id=installation_id,
        )
        return pull_request


@deprecated(
    breaking_version="0.27",
    additional_warn_text=(
        "`GithubResource` is deprecated. Use your own resource instead. "
        "Learn how to create your own resource here: "
        "https://docs.dagster.io/guides/build/external-resources/defining-resources"
    ),
)
class GithubResource(ConfigurableResource):
    """A resource configuration class for GitHub integration.

    This class provides configuration fields for setting up a GitHub Application,
    including the application ID, private RSA key, installation ID, and hostname.

    Args:
        github_app_id (int): The GitHub Application ID. For more information, see
            https://developer.github.com/apps/.
        github_app_private_rsa_key (str): The private RSA key text for the GitHub Application.
            For more information, see https://developer.github.com/apps/.
        github_installation_id (Optional[int]): The GitHub Application Installation ID.
            Defaults to None. For more information, see https://developer.github.com/apps/.
        github_hostname (Optional[str]): The GitHub hostname. Defaults to `api.github.com`.
            For more information, see https://developer.github.com/apps/.
    """

    github_app_id: int = Field(
        description="Github Application ID, for more info see https://developer.github.com/apps/",
    )
    github_app_private_rsa_key: str = Field(
        description=(
            "Github Application Private RSA key text, for more info see"
            " https://developer.github.com/apps/"
        ),
    )
    github_installation_id: Optional[int] = Field(
        default=None,
        description=(
            "Github Application Installation ID, for more info see"
            " https://developer.github.com/apps/"
        ),
    )
    github_hostname: Optional[str] = Field(
        default=None,
        description=(
            "Github hostname. Defaults to `api.github.com`, for more info see"
            " https://developer.github.com/apps/"
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @public
    def get_client(self) -> GithubClient:
        """Instantiate and return a GitHub client.

        This method creates a new instance of `GithubClient` using the configuration
        attributes of the `GithubResource` instance. The client is initialized with
        an authenticated session and the necessary credentials for interacting with
        the GitHub API.

        Returns:
            GithubClient: An instance of `GithubClient` configured with the current resource settings.
        """
        return GithubClient(
            client=requests.Session(),
            app_id=self.github_app_id,
            app_private_rsa_key=self.github_app_private_rsa_key,
            default_installation_id=self.github_installation_id,
            hostname=self.github_hostname,
        )


@deprecated(
    breaking_version="0.27",
    additional_warn_text=(
        "`github_resource` is deprecated. Use your own resource instead. "
        "Learn how to create your own resource here: "
        "https://docs.dagster.io/guides/build/external-resources/defining-resources"
    ),
)
@dagster_maintained_resource
@resource(
    config_schema=GithubResource.to_config_schema(),
    description="This resource is for connecting to Github",
)
def github_resource(context) -> GithubClient:
    return GithubResource(**context.resource_config).get_client()
