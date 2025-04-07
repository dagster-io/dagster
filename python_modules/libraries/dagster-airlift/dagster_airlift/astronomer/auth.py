"""Astronomer authentication backends for Apache Airflow."""

from typing import Any, Optional, Dict

import requests
from dagster._annotations import beta
from dagster_airlift.core.airflow_instance import AirflowAuthBackend


@beta
class AstronomerSessionAuthBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates to Astronomer Cloud.

    This class handles authentication to an Astronomer-hosted Airflow instance using username/password
    credentials. It manages session cookies for subsequent requests to the Astronomer API.

    Args:
        deployment_hostname (str): The hostname for the Astronomer deployment 
            (e.g., "deployment-name.astronomer.run")
        username (str): The username for authentication
        password (str): The password for authentication
    """

    def __init__(self, deployment_hostname: str, username: str, password: str) -> None:
        self.deployment_hostname = deployment_hostname
        self.username = username
        self.password = password
        self._session: Optional[requests.Session] = None

    def get_session(self) -> requests.Session:
        """Returns an authenticated session for the Astronomer deployment.

        Creates and authenticates a new session if one doesn't exist. The session includes
        all necessary cookies for authentication.

        Returns:
            requests.Session: An authenticated session
        """
        if self._session is None:
            self._session = requests.Session()
            login_url = f"https://{self.deployment_hostname}/oauth/token"
            
            # Create login payload
            data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
            
            # Authenticate and get session token
            response = self._session.post(login_url, data=data)
            response.raise_for_status()
            
            # Extract the access token from the response
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            # Set the authorization header for subsequent requests
            self._session.headers.update({"Authorization": f"Bearer {access_token}"})
        
        return self._session

    def get_webserver_url(self) -> str:
        """Returns the base URL for the Astronomer webserver.

        Returns:
            str: The webserver URL
        """
        return f"https://{self.deployment_hostname}"


@beta
class AstronomerApiKeyAuthBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates to Astronomer Cloud using API keys.

    This class handles authentication to an Astronomer-hosted Airflow instance using API key
    authentication. It's suitable for automated processes where username/password authentication
    isn't appropriate.

    Args:
        deployment_hostname (str): The hostname for the Astronomer deployment 
            (e.g., "deployment-name.astronomer.run")
        api_key (str): The API key generated from Astronomer Cloud
    """

    def __init__(self, deployment_hostname: str, api_key: str) -> None:
        self.deployment_hostname = deployment_hostname
        self.api_key = api_key
        self._session: Optional[requests.Session] = None

    def get_session(self) -> requests.Session:
        """Returns an authenticated session for the Astronomer deployment.

        Creates a new session with the API key in the authorization header if one doesn't exist.

        Returns:
            requests.Session: An authenticated session
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        return self._session

    def get_webserver_url(self) -> str:
        """Returns the base URL for the Astronomer webserver.

        Returns:
            str: The webserver URL
        """
        return f"https://{self.deployment_hostname}"