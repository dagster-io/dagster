import requests
from dagster._annotations import beta

from dagster_airlift.core.airflow_instance import AirflowAuthBackend


@beta
class AirflowBasicAuthBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates using basic auth.

    Args:
        webserver_url (str): The URL of the webserver.
        username (str): The username to authenticate with.
        password (str): The password to authenticate with.

    Examples:
        Creating a :py:class:`AirflowInstance` using this backend.

        .. code-block:: python

            from dagster_airlift.core import AirflowInstance, AirflowBasicAuthBackend

            af_instance = AirflowInstance(
                name="my-instance",
                auth_backend=AirflowBasicAuthBackend(
                    webserver_url="https://my-webserver-hostname",
                    username="my-username",
                    password="my-password"
                )
            )

    """

    def __init__(self, webserver_url: str, username: str, password: str):
        self._webserver_url = webserver_url
        self.username = username
        self.password = password

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (self.username, self.password)
        return session

    def get_webserver_url(self) -> str:
        return self._webserver_url
