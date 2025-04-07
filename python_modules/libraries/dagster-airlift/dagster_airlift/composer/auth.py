from typing import Any, Optional

import google.auth
from google.auth.transport.requests import AuthorizedSession
from dagster._annotations import beta

from dagster_airlift.core.airflow_instance import AirflowAuthBackend


@beta
class ComposerSessionAuthBackend(AirflowAuthBackend):
    """A :py:class:`dagster_airlift.core.AirflowAuthBackend` that authenticates to Google Cloud Composer.

    Under the hood, this class uses Google Cloud authentication to create an authorized session
    to interact with the Composer Airflow webserver.

    Args:
        project_id (str): The Google Cloud project ID
        region (str): The Google Cloud region
        environment_name (str): The name of the Composer environment
        credentials (Optional[google.auth.credentials.Credentials]): Optional Google Cloud credentials.
            If not provided, the default credentials will be used.

    Examples:
        Creating an AirflowInstance pointed at a Composer environment.

        .. code-block:: python

            from dagster_airlift.composer import ComposerSessionAuthBackend
            from dagster_airlift.core import AirflowInstance

            af_instance = AirflowInstance(
                name="my-composer-instance",
                auth_backend=ComposerSessionAuthBackend(
                    project_id="my-gcp-project",
                    region="us-central1",
                    environment_name="my-composer-env"
                )
            )
    """

    def __init__(
        self,
        project_id: str,
        region: str,
        environment_name: str,
        credentials: Optional[Any] = None,
    ) -> None:
        self.project_id = project_id
        self.region = region
        self.environment_name = environment_name
        self._credentials = credentials
        self._webserver_url = None

    @staticmethod
    def from_service_account(
        project_id: str, 
        region: str, 
        environment_name: str, 
        service_account_file: str
    ) -> "ComposerSessionAuthBackend":
        """Create a ComposerSessionAuthBackend from a service account file.

        Args:
            project_id (str): The Google Cloud project ID
            region (str): The Google Cloud region
            environment_name (str): The name of the Composer environment
            service_account_file (str): Path to the service account file

        Returns:
            ComposerSessionAuthBackend: A configured auth backend
        """
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return ComposerSessionAuthBackend(
            project_id=project_id, 
            region=region, 
            environment_name=environment_name, 
            credentials=credentials
        )

    def _get_composer_webserver_url(self) -> str:
        """Get the webserver URL for the Composer environment."""
        from google.cloud import composer_v1

        if self._credentials:
            client = composer_v1.EnvironmentsClient(credentials=self._credentials)
        else:
            client = composer_v1.EnvironmentsClient()

        environment_path = client.environment_path(
            self.project_id, self.region, self.environment_name
        )
        environment = client.get_environment(name=environment_path)
        return environment.config.airflow_uri

    def get_session(self) -> AuthorizedSession:
        """Returns an authenticated session for the Composer environment."""
        if not self._credentials:
            # Get default credentials (uses service account or user credentials)
            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        else:
            credentials = self._credentials
        
        # Create an authorized session
        session = AuthorizedSession(credentials)
        return session

    def get_webserver_url(self) -> str:
        """Returns the Airflow webserver URL for the Composer environment."""
        if not self._webserver_url:
            self._webserver_url = self._get_composer_webserver_url()
        return self._webserver_url