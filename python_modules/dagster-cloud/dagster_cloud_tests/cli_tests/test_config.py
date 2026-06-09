import json
import os
import queue
import tempfile
import threading
import time
from unittest import mock

import pytest
import requests
from click import Command
from dagster._core.test_utils import environ
from dagster_cloud_cli import config_utils
from dagster_cloud_cli.commands.config import SetupAuthMethod, app, app_configure
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.yaml_utils import safe_load_yaml
from typer import Context
from typer.testing import CliRunner


@pytest.fixture
def test_config_file():
    with (
        tempfile.TemporaryDirectory() as dagster_cloud_tmpdir,
        tempfile.TemporaryDirectory() as dg_tmpdir,
    ):
        dagster_cloud_config_path = os.path.join(dagster_cloud_tmpdir, "config")
        dg_config_path = os.path.join(dg_tmpdir, "dg.toml")
        with environ(
            {
                "DAGSTER_CLOUD_CLI_CONFIG": dagster_cloud_config_path,
                "DG_CLI_CONFIG": dg_config_path,
            }
        ):
            yield dagster_cloud_config_path


@pytest.fixture
def populated_config(test_config_file):
    with open(test_config_file, "w", encoding="utf8") as f:
        f.write(
            """
organization: acme
default_deployment: staging
user_token: xyz123
        """
        )


@pytest.fixture
def populated_dg_config(test_config_file):
    test_dg_config_file = os.getenv("DG_CLI_CONFIG")
    assert test_dg_config_file is not None
    with open(test_dg_config_file, "w", encoding="utf8") as f:
        f.write(
            """[cli.plus]
organization = "bcme"
default_deployment = "prod"
user_token = "abc123"
        """
        )


def test_read_write_config(test_config_file):
    config = DagsterPlusCliConfig(
        organization="elementl", default_deployment="prod", user_token="abc123"
    )
    config_utils.write_config(config)

    read_config = config_utils.read_config()

    assert read_config.organization == "elementl"
    assert read_config.default_deployment == "prod"
    assert read_config.user_token == "abc123"


def test_overrides(populated_config):
    assert config_utils.get_organization() == "acme"
    assert config_utils.get_deployment() == "staging"
    assert config_utils.get_user_token() == "xyz123"
    assert config_utils.get_url() is None

    with environ(
        {
            "DAGSTER_CLOUD_ORGANIZATION": "elementl",
            "DAGSTER_CLOUD_DEPLOYMENT": "prod",
            "DAGSTER_CLOUD_API_TOKEN": "abc123",
            "DAGSTER_CLOUD_URL": "localhost:3000",
        }
    ):
        assert config_utils.get_organization() == "elementl"
        assert config_utils.get_deployment() == "prod"
        assert config_utils.get_user_token() == "abc123"
        assert config_utils.get_url() == "localhost:3000"

        ctx = Context(Command("test"))
        ctx.params["organization"] = "test"
        ctx.params["deployment"] = "dev"
        ctx.params["api_token"] = "def456"
        ctx.params["url"] = "localhost:4000"

        assert config_utils.get_organization(ctx) == "test"
        assert config_utils.get_deployment(ctx) == "dev"
        assert config_utils.get_user_token(ctx) == "def456"
        assert config_utils.get_url(ctx) == "localhost:4000"


def test_view_command(populated_config):
    runner = CliRunner()
    result = runner.invoke(app, ["view"])

    assert result.exit_code == 0, result.output + " : " + str(result.exception)

    assert safe_load_yaml(result.output) == {
        "organization": "acme",
        "default_deployment": "staging",
        "user_token": "xyz123",
    }


def test_view_command_using_dg_config(populated_dg_config):
    runner = CliRunner()
    result = runner.invoke(app, ["view"])

    assert result.exit_code == 0, result.output + " : " + str(result.exception)

    assert safe_load_yaml(result.output) == {
        "organization": "bcme",
        "default_deployment": "prod",
        "user_token": "abc123",
    }


def test_view_command_using_both_configs(populated_config, populated_dg_config):
    runner = CliRunner()
    result = runner.invoke(app, ["view"])

    # We loudly error if a user has config in both places, to avoid silently performing unexpected behavior
    assert result.exit_code == 1, "Found Dagster Plus config in both" in result.output


# Test setup command, using the CLI auth option
def test_setup_command_cli(test_config_file):
    runner = CliRunner()

    with mock.patch(
        "dagster_cloud_cli.commands.config._settings_method_input",
        mock.Mock(return_value=SetupAuthMethod.CLI),
    ):
        # First, we test the case where a GraphQL call to get the deployments list fails
        # This prompts the user for a text input
        with mock.patch(
            "dagster_cloud_cli.commands.config.gql.fetch_full_deployments",
            mock.Mock(return_value=Exception()),
        ):
            # Ensure initial configure works
            input_mock = mock.Mock(
                side_effect=[
                    "hooli",  # organization
                    "prod",  # deployment
                ]
            )
            password_input_mock = mock.Mock(
                side_effect=[
                    "abc123",  # password
                ],
            )
            with (
                mock.patch("dagster_cloud_cli.commands.config.ui.input", input_mock),
                mock.patch(
                    "dagster_cloud_cli.commands.config.ui.password_input",
                    password_input_mock,
                ),
            ):
                result = runner.invoke(app, ["setup"])

            assert result.exit_code == 0, result.output + " : " + str(result.exception)

            # Verify defaults were as expected
            input_mock.assert_has_calls(
                [mock.call(mock.ANY, default=""), mock.call(mock.ANY, default="")]
            )
            password_input_mock.assert_has_calls([mock.call(mock.ANY, default="")])

            # Verify new configuraiton success
            assert config_utils.get_organization() == "hooli"
            assert config_utils.get_deployment() == "prod"
            assert config_utils.get_user_token() == "abc123"

            # Verify we can reconfigure the CLI, with old defaults
            input_mock = mock.Mock(
                side_effect=[
                    "hooli",  # organization
                    "staging",  # deployment
                ]
            )
            password_input_mock = mock.Mock(
                side_effect=["def456"],  # password
            )
            with (
                mock.patch("dagster_cloud_cli.commands.config.ui.input", input_mock),
                mock.patch(
                    "dagster_cloud_cli.commands.config.ui.password_input",
                    password_input_mock,
                ),
            ):
                result = runner.invoke(app, ["setup"])

            assert result.exit_code == 0, result.output + " : " + str(result.exception)

            # Verify defaults were as expected
            input_mock.assert_has_calls(
                [
                    mock.call(mock.ANY, default="hooli"),
                    mock.call(mock.ANY, default="prod"),
                ]
            )
            password_input_mock.assert_has_calls([mock.call(mock.ANY, default="abc123")])

            # Verify new configuraiton success
            assert config_utils.get_organization() == "hooli"
            assert config_utils.get_deployment() == "staging"
            assert config_utils.get_user_token() == "def456"

        # Next, test when deployment list is returned successfully
        # This prompts a list input, with the default being the existing deployment
        with mock.patch(
            "dagster_cloud_cli.commands.config.gql.fetch_full_deployments",
            mock.Mock(return_value=[{"deploymentName": "prod"}, {"deploymentName": "staging"}]),
        ):
            # Verify we can reconfigure the CLI, with old defaults

            input_mock = mock.Mock(side_effect=["hooli"])  # organization
            password_input_mock = mock.Mock(side_effect=["abc123"])  # user token
            list_input_mock = mock.Mock(side_effect=["prod"])  # deployment

            with (
                mock.patch("dagster_cloud_cli.commands.config.ui.input", input_mock),
                mock.patch(
                    "dagster_cloud_cli.commands.config.ui.password_input",
                    password_input_mock,
                ),
                mock.patch("dagster_cloud_cli.commands.config.ui.list_input", list_input_mock),
            ):
                result = runner.invoke(app, ["setup"])

            assert result.exit_code == 0, result.output + " : " + str(result.exception)

            # Verify defaults were as expected
            input_mock.assert_has_calls([mock.call(mock.ANY, default="hooli")])
            password_input_mock.assert_has_calls([mock.call(mock.ANY, default="def456")])
            list_input_mock.assert_has_calls(
                [mock.call(mock.ANY, choices=["None", "prod", "staging"], default="staging")]
            )

            # Verify new configuraiton success
            assert config_utils.get_organization() == "hooli"
            assert config_utils.get_deployment() == "prod"
            assert config_utils.get_user_token() == "abc123"

        # Sanity check that if the current deployment is not in the list, it is not passed as default
        # Also test backcompat with `dagster-cloud configure`
        with mock.patch(
            "dagster_cloud_cli.commands.config.gql.fetch_full_deployments",
            mock.Mock(
                return_value=[
                    {"deploymentName": "staging"},
                    {"deploymentName": "releasing"},
                ]
            ),
        ):
            input_mock = mock.Mock(side_effect=["elementl"])  # organization
            password_input_mock = mock.Mock(side_effect=["def456"])  # user token
            list_input_mock = mock.Mock(side_effect=["releasing"])  # deployment

            with (
                mock.patch("dagster_cloud_cli.commands.config.ui.input", input_mock),
                mock.patch(
                    "dagster_cloud_cli.commands.config.ui.password_input",
                    password_input_mock,
                ),
                mock.patch("dagster_cloud_cli.commands.config.ui.list_input", list_input_mock),
            ):
                result = runner.invoke(app_configure, [])

            assert result.exit_code == 0, result.output + " : " + str(result.exception)

            # Verify defaults were as expected
            input_mock.assert_has_calls([mock.call(mock.ANY, default="hooli")])
            password_input_mock.assert_has_calls([mock.call(mock.ANY, default="abc123")])
            list_input_mock.assert_has_calls(
                [
                    mock.call(
                        mock.ANY,
                        choices=["None", "staging", "releasing"],
                        default="None",
                    )
                ]
            )

            # Verify new configuraiton success
            assert config_utils.get_organization() == "elementl"
            assert config_utils.get_deployment() == "releasing"
            assert config_utils.get_user_token() == "def456"


# Test setup command, using the web auth option
def test_setup_command_web(test_config_file):
    runner = CliRunner()

    with (
        mock.patch(
            "dagster_shared.utils.find_free_port",
            mock.Mock(return_value=4000),
        ),
        mock.patch(
            "dagster_shared.plus.login_server._generate_nonce",
            mock.Mock(return_value="ABCDEFGH"),
        ),
        mock.patch(
            "dagster_cloud_cli.commands.config.webbrowser.open",
            mock.Mock(return_value=True),
        ),
        mock.patch(
            "dagster_cloud_cli.commands.config._settings_method_input",
            mock.Mock(return_value=SetupAuthMethod.WEB),
        ),
        mock.patch(
            "dagster_cloud_cli.commands.config.gql.fetch_full_deployments",
            mock.Mock(return_value=[{"deploymentName": "prod"}, {"deploymentName": "staging"}]),
        ),
    ):
        assert config_utils.get_organization() is None
        assert config_utils.get_deployment() is None
        assert config_utils.get_user_token() is None

        # Send configuration response to CLI endpoint, HTTP response passed back in queue
        q = queue.Queue()

        def respond_with_callback():
            time.sleep(0.25)
            response = requests.post(
                "http://localhost:4000/callback",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"nonce": "ABCDEFGH", "organization": "hooli", "token": "abc123"}),
            )
            q.put(response)

        th = threading.Thread(target=respond_with_callback)
        th.start()

        # Verify that the CLI is reconfigured by hitting the callback endpoint
        list_input_mock = mock.Mock(side_effect=["prod"])  # deployment

        with mock.patch("dagster_cloud_cli.commands.config.ui.list_input", list_input_mock):
            result = runner.invoke(app, ["setup"])
        th.join()

        assert result.exit_code == 0, result.output + " : " + str(result.exception)

        assert q.get().json().get("ok") is True, "JSON response from callback not as expected"

        # Verify defaults were as expected
        list_input_mock.assert_has_calls(
            [mock.call(mock.ANY, choices=["None", "prod", "staging"], default="None")]
        )

        # Verify new configuration success
        assert config_utils.get_organization() == "hooli"
        assert config_utils.get_deployment() == "prod"
        assert config_utils.get_user_token() == "abc123"


def test_setup_command_interrupt(test_config_file):
    runner = CliRunner()

    # Ensure keyboard interrupt stops execution
    input_mock = mock.Mock(
        side_effect=[
            "hooli",  # organization
        ]
    )
    with (
        mock.patch("dagster_cloud_cli.commands.config.ui.input", input_mock),
        mock.patch(
            "dagster_cloud_cli.commands.config.ui.password_input",
            side_effect=KeyboardInterrupt,
        ),
    ):
        result = runner.invoke(app, ["setup"])

    assert result.exit_code == 1, result.output + " : " + str(result.exception)

    # Verify no new configuraiton
    assert config_utils.get_organization() is None
    assert config_utils.get_deployment() is None
    assert config_utils.get_user_token() is None


def test_set_deployment_command(populated_config):
    with mock.patch(
        "dagster_cloud_cli.commands.config.available_deployment_names"
    ) as available_deployment_names:
        assert config_utils.get_deployment() == "staging"
        available_deployment_names.return_value = ["prod", "staging"]

        # Verify we can switch deployment to prod
        runner = CliRunner()
        result = runner.invoke(app, ["set-deployment", "prod"])

        assert result.exit_code == 0, result.output + " : " + str(result.exception)
        assert config_utils.get_deployment() == "prod"

        # Verify we can't switch deployment to fake
        runner = CliRunner()
        result = runner.invoke(app, ["set-deployment", "fake"])

        assert result.exit_code == 1, result.output + " : " + str(result.exception)
        assert config_utils.get_deployment() == "prod"
