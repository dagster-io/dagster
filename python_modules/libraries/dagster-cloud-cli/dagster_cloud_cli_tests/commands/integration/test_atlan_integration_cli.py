import validators
from dagster_cloud_cli.entrypoint import app
from typer.testing import CliRunner

FAKE_TOKEN = "fake_token"
FAKE_DOMAIN = "fake-domain.com"


def test_dagster_cloud_atlan_integration_set_settings(empty_config, monkeypatch, mocker) -> None:
    """Tests Atlan set-settings CLI."""
    set_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.set_atlan_integration_settings",
        return_value=("fake-organization", True),
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


def test_dagster_cloud_atlan_integration_set_settings_exception(
    empty_config, monkeypatch, mocker
) -> None:
    """Tests exception in Atlan set-settings CLI."""
    set_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.set_atlan_integration_settings", side_effect=Exception()
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
    assert result.exit_code
    set_atlan_integration_settings.assert_called_once()
    _, kwargs = set_atlan_integration_settings.call_args_list[0]
    assert kwargs["token"] == FAKE_TOKEN
    assert kwargs["domain"] == FAKE_DOMAIN


def test_dagster_cloud_atlan_integration_set_settings_domain_validation_error(
    empty_config, monkeypatch, mocker
) -> None:
    """Tests domain validation error in Atlan set-settings CLI."""
    invalid_domain = f"https://{FAKE_DOMAIN}"

    validate_domain = mocker.patch(
        "dagster_cloud_cli.commands.integration.atlan.validators.domain",
        return_value=validators.ValidationError(
            function=validators.domain, arg_dict={"value": invalid_domain}
        ),
    )

    set_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.set_atlan_integration_settings",
        side_effect=validators.ValidationError(
            function=validators.domain, arg_dict={"value": invalid_domain}
        ),
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "set-settings", FAKE_TOKEN, invalid_domain, "--url", "fake-url"],
        env=env,
    )
    assert result.exit_code
    validate_domain.assert_called_once()
    args, _ = validate_domain.call_args_list[0]
    assert args[0] == invalid_domain
    set_atlan_integration_settings.assert_not_called()


def test_dagster_cloud_atlan_integration_delete_settings(empty_config, monkeypatch, mocker) -> None:
    """Tests Atlan delete-settings CLI."""
    delete_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.delete_atlan_integration_settings",
        return_value=("fake-organization", True),
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "delete-settings", "--url", "fake-url"],
        env=env,
    )
    assert not result.exit_code
    delete_atlan_integration_settings.assert_called_once()


def test_dagster_cloud_atlan_integration_get_settings(empty_config, monkeypatch, mocker) -> None:
    """Tests Atlan get-settings CLI."""
    get_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.get_atlan_integration_settings",
        return_value={"token": FAKE_TOKEN, "domain": FAKE_DOMAIN},
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "get-settings", "--url", "fake-url"],
        env=env,
    )
    assert not result.exit_code
    get_atlan_integration_settings.assert_called_once()
    assert FAKE_TOKEN in result.output
    assert FAKE_DOMAIN in result.output


def test_dagster_cloud_atlan_integration_preflight_check_success(
    empty_config, monkeypatch, mocker
) -> None:
    """Tests Atlan preflight-check CLI with success."""
    atlan_integration_preflight_check = mocker.patch(
        "dagster_cloud_cli.gql.atlan_integration_preflight_check",
        return_value={"success": True},
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "preflight-check", "--url", "fake-url"],
        env=env,
    )
    assert not result.exit_code
    atlan_integration_preflight_check.assert_called_once()
    assert "passed successfully" in result.output


def test_dagster_cloud_atlan_integration_preflight_check_failure(
    empty_config, monkeypatch, mocker
) -> None:
    """Tests Atlan preflight-check CLI with failure."""
    atlan_integration_preflight_check = mocker.patch(
        "dagster_cloud_cli.gql.atlan_integration_preflight_check",
        return_value={
            "success": False,
            "error_code": "TEST_ERROR",
            "error_message": "Test error message",
        },
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "preflight-check", "--url", "fake-url"],
        env=env,
    )
    assert not result.exit_code
    atlan_integration_preflight_check.assert_called_once()
    assert "failed" in result.output
    assert "TEST_ERROR" in result.output
    assert "Test error message" in result.output


def test_dagster_cloud_atlan_integration_delete_settings_exception(
    empty_config, monkeypatch, mocker
) -> None:
    """Tests Atlan delete-settings CLI."""
    delete_atlan_integration_settings = mocker.patch(
        "dagster_cloud_cli.gql.delete_atlan_integration_settings", side_effect=Exception()
    )

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["integration", "atlan", "delete-settings", "--url", "fake-url"],
        env=env,
    )
    assert result.exit_code
    delete_atlan_integration_settings.assert_called_once()
