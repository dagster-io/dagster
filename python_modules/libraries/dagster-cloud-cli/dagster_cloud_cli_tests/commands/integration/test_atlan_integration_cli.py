from dagster_cloud_cli.entrypoint import app
from typer.testing import CliRunner

FAKE_TOKEN = "fake_token"
FAKE_DOMAIN = "fake_domain"


def test_dagster_cloud_atlan_integration_set_settings(empty_config, monkeypatch, mocker) -> None:
    """Tests Atlan set-settings CLI."""
    set_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.set_atlan_integration_settings"
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "set-settings", FAKE_TOKEN, FAKE_DOMAIN, "--url", "fake-url"],
        env=env,
    )
    assert not result.exit_code
    set_atlan_integration_settings.assert_called_once()
    _, kwargs = set_atlan_integration_settings.call_args_list[0]
    assert kwargs["token"] == FAKE_TOKEN
    assert kwargs["domain"] == FAKE_DOMAIN
