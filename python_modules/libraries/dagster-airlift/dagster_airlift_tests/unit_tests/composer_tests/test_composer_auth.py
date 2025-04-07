import unittest
from unittest import mock

from google.auth.transport.requests import AuthorizedSession
from google.cloud.composer_v1.types import Environment, EnvironmentConfig

from dagster_airlift.composer import ComposerSessionAuthBackend


class TestComposerSessionAuthBackend(unittest.TestCase):
    def setUp(self):
        # Mock environment configuration with Airflow URI
        self.mock_environment = Environment(
            config=EnvironmentConfig(airflow_uri="https://example-composer.com")
        )
        
        # Mock the composer client
        self.mock_client_patcher = mock.patch("google.cloud.composer_v1.EnvironmentsClient")
        self.mock_client = self.mock_client_patcher.start()
        
        # Set up the mock client to return our mock environment
        self.mock_client_instance = self.mock_client.return_value
        self.mock_client_instance.get_environment.return_value = self.mock_environment
        self.mock_client_instance.environment_path.return_value = "projects/test/locations/us-central1/environments/test-env"

        # Mock google.auth.default
        self.mock_auth_patcher = mock.patch("google.auth.default")
        self.mock_auth = self.mock_auth_patcher.start()
        self.mock_credentials = mock.Mock()
        self.mock_auth.return_value = (self.mock_credentials, "project-id")

        # Mock AuthorizedSession
        self.mock_session_patcher = mock.patch("google.auth.transport.requests.AuthorizedSession")
        self.mock_session = self.mock_session_patcher.start()
        self.mock_session_instance = self.mock_session.return_value

    def tearDown(self):
        self.mock_client_patcher.stop()
        self.mock_auth_patcher.stop()
        self.mock_session_patcher.stop()

    def test_get_webserver_url(self):
        """Test that get_webserver_url returns the correct URL from the Composer API."""
        auth_backend = ComposerSessionAuthBackend(
            project_id="test",
            region="us-central1",
            environment_name="test-env",
        )
        
        # Get the webserver URL
        webserver_url = auth_backend.get_webserver_url()
        
        # Verify the URL is correct
        self.assertEqual(webserver_url, "https://example-composer.com")
        
        # Verify that the client was called correctly
        self.mock_client_instance.environment_path.assert_called_once_with(
            "test", "us-central1", "test-env"
        )
        self.mock_client_instance.get_environment.assert_called_once_with(
            name="projects/test/locations/us-central1/environments/test-env"
        )

    def test_get_session(self):
        """Test that get_session returns an authenticated session."""
        auth_backend = ComposerSessionAuthBackend(
            project_id="test",
            region="us-central1",
            environment_name="test-env",
        )
        
        # Get the session
        session = auth_backend.get_session()
        
        # Verify that google.auth.default was called with the correct scopes
        self.mock_auth.assert_called_once_with(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # Verify that AuthorizedSession was called with the credentials
        self.mock_session.assert_called_once_with(self.mock_credentials)
        
        # Verify the session is an AuthorizedSession
        self.assertEqual(session, self.mock_session_instance)

    def test_from_service_account(self):
        """Test creating auth backend from service account file."""
        with mock.patch("google.oauth2.service_account.Credentials") as mock_creds:
            mock_creds.from_service_account_file.return_value = self.mock_credentials
            
            auth_backend = ComposerSessionAuthBackend.from_service_account(
                project_id="test", 
                region="us-central1",
                environment_name="test-env",
                service_account_file="/path/to/service_account.json"
            )
            
            # Verify service account credentials were loaded
            mock_creds.from_service_account_file.assert_called_once_with(
                "/path/to/service_account.json",
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
            # Verify the backend was created with the credentials
            self.assertEqual(auth_backend.project_id, "test")
            self.assertEqual(auth_backend.region, "us-central1")
            self.assertEqual(auth_backend.environment_name, "test-env")
            self.assertEqual(auth_backend._credentials, self.mock_credentials)
            
    def test_with_explicit_credentials(self):
        """Test that the backend works with explicitly provided credentials."""
        explicit_credentials = mock.Mock()
        
        auth_backend = ComposerSessionAuthBackend(
            project_id="test",
            region="us-central1",
            environment_name="test-env",
            credentials=explicit_credentials
        )
        
        # Get the session
        session = auth_backend.get_session()
        
        # Verify that google.auth.default was NOT called
        self.mock_auth.assert_not_called()
        
        # Verify that AuthorizedSession was called with the explicit credentials
        self.mock_session.assert_called_once_with(explicit_credentials)