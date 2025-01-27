from typing import Any, Optional

import boto3
import requests
from dagster._annotations import beta

from dagster_airlift.core.airflow_instance import AirflowAuthBackend


def get_session_info(mwaa: Any, env_name: str) -> tuple[str, str]:
    # Initialize MWAA client and request a web login token
    response = mwaa.create_web_login_token(Name=env_name)

    # Extract the web server hostname and login token
    web_server_host_name = response["WebServerHostname"]
    web_token = response["WebToken"]

    # Construct the URL needed for authentication
    login_url = f"https://{web_server_host_name}/aws_mwaa/login"
    login_payload = {"token": web_token}

    # Make a POST request to the MWAA login url using the login payload
    response = requests.post(login_url, data=login_payload, timeout=10)

    # Check if login was succesfull
    if response.status_code == 200:
        # Return the hostname and the session cookie
        return (web_server_host_name, response.cookies["session"])
    else:
        raise Exception(f"Failed to get session info: {response.text}")


@beta
class MwaaSessionAuthBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates to AWS MWAA.

    Under the hood, this class uses the MWAA boto3 session to request a web login token and then
    uses the token to authenticate to the MWAA web server.

    Args:
        mwaa_session (boto3.Session): The boto3 MWAA session
        env_name (str): The name of the MWAA environment

    Examples:
        Creating an AirflowInstance pointed at a MWAA environment.

        .. code-block:: python

            import boto3
            from dagster_airlift.mwaa import MwaaSessionAuthBackend
            from dagster_airlift.core import AirflowInstance

            boto_client = boto3.client("mwaa")
            af_instance = AirflowInstance(
                name="my-mwaa-instance",
                auth_backend=MwaaSessionAuthBackend(
                    mwaa_client=boto_client,
                    env_name="my-mwaa-env"
                )
            )

    """

    def __init__(self, mwaa_client: Any, env_name: str) -> None:
        self.mwaa_client = mwaa_client
        self.env_name = env_name
        # Session info is generated when we either try to retrieve a session or retrieve the web server url
        self._session_info: Optional[tuple[str, str]] = None

    @staticmethod
    def from_profile(region: str, env_name: str, profile_name: Optional[str] = None):
        boto_session = boto3.Session(profile_name=profile_name, region_name=region)
        mwaa = boto_session.client("mwaa")
        return MwaaSessionAuthBackend(mwaa_client=mwaa, env_name=env_name)

    def get_session(self) -> requests.Session:
        # Get the session info
        if not self._session_info:
            self._session_info = get_session_info(mwaa=self.mwaa_client, env_name=self.env_name)
        session_cookie = self._session_info[1]
        # Create a new session
        session = requests.Session()
        session.cookies.set("session", session_cookie)

        # Return the session
        return session

    def get_webserver_url(self) -> str:
        if not self._session_info:
            self._session_info = get_session_info(mwaa=self.mwaa_client, env_name=self.env_name)
        return f"https://{self._session_info[0]}"
