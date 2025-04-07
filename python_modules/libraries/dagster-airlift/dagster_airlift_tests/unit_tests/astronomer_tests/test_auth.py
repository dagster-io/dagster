"""Tests for Astronomer authentication backends."""

import pytest
import requests
import responses
from requests import Session

from dagster_airlift.astronomer.auth import AstronomerApiKeyAuthBackend, AstronomerSessionAuthBackend


@pytest.fixture
def mock_responses():
    """Fixture to set up and tear down the responses mock."""
    with responses.RequestsMock() as rsps:
        yield rsps


def test_astronomer_session_auth_backend(mock_responses):
    """Test the AstronomerSessionAuthBackend class."""
    # Set up
    deployment_hostname = "test-deployment.astronomer.run"
    username = "test-user"
    password = "test-password"
    webserver_url = f"https://{deployment_hostname}"
    
    # Mock the login endpoint
    mock_responses.add(
        responses.POST,
        f"{webserver_url}/oauth/token",
        json={"access_token": "test-token", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )
    
    # Create the auth backend
    auth_backend = AstronomerSessionAuthBackend(
        deployment_hostname=deployment_hostname,
        username=username,
        password=password,
    )
    
    # Test get_webserver_url
    assert auth_backend.get_webserver_url() == webserver_url
    
    # Test get_session
    session = auth_backend.get_session()
    assert isinstance(session, Session)
    assert session.headers.get("Authorization") == "Bearer test-token"
    
    # Check that the mocked endpoint was called with the correct data
    assert len(mock_responses.calls) == 1
    assert mock_responses.calls[0].request.url == f"{webserver_url}/oauth/token"
    assert "username=test-user" in mock_responses.calls[0].request.body
    assert "password=test-password" in mock_responses.calls[0].request.body
    assert "grant_type=password" in mock_responses.calls[0].request.body


def test_astronomer_api_key_auth_backend():
    """Test the AstronomerApiKeyAuthBackend class."""
    # Set up
    deployment_hostname = "test-deployment.astronomer.run"
    api_key = "test-api-key"
    webserver_url = f"https://{deployment_hostname}"
    
    # Create the auth backend
    auth_backend = AstronomerApiKeyAuthBackend(
        deployment_hostname=deployment_hostname,
        api_key=api_key,
    )
    
    # Test get_webserver_url
    assert auth_backend.get_webserver_url() == webserver_url
    
    # Test get_session
    session = auth_backend.get_session()
    assert isinstance(session, Session)
    assert session.headers.get("Authorization") == f"Bearer {api_key}"