import mock
from dagster_airlift.mwaa import MwaaSessionAuthBackend


def test_mwaa_session_auth() -> None:
    """Test output format of mwaa auth backend. Does not actually make any live requests to boto or exercise usage of aws apis in any way."""
    with mock.patch("dagster_airlift.mwaa.auth_backend.get_session_info") as mock_get_session_info:
        mock_get_session_info.return_value = ("my-webserver-hostname", "my-session-cookie")
        auth_backend = MwaaSessionAuthBackend(region="us-west-2", env_name="my-env")
        session = auth_backend.get_session()
        assert session.cookies["session"] == "my-session-cookie"
        assert auth_backend.get_webserver_url() == "https://my-webserver-hostname"
