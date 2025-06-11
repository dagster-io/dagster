import requests
from dagster._annotations import beta

from dagster_airlift.core.airflow_instance import AirflowAuthBackend


@beta
class AirflowBearerTokenBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates using a bearer token.

    Args:
        webserver_url (str): The URL of the webserver.
        token (str): The bearer token to authenticate with.

    Examples:
        Creating a :py:class:`AirflowInstance` using this backend.

        .. code-block:: python

            from dagster_airlift.core import AirflowInstance
            from dagster_airlift.core.token_backend import AirflowBearerTokenBackend

            af_instance = AirflowInstance(
                name="my-instance",
                auth_backend=AirflowBearerTokenBackend(
                    webserver_url="https://my-webserver-hostname",
                    token="my-bearer-token"
                )
            )

    """

    def __init__(self, webserver_url: str, token: str):
        self._webserver_url = webserver_url
        self.token = token

    def get_session(self) -> requests.Session:
        # Eventually we want to make sure to cache this with a TTL
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self.token}"})
        return session

    def get_webserver_url(self) -> str:
        return self._webserver_url
