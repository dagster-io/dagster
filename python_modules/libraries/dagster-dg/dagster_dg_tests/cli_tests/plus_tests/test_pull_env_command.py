import tempfile
from pathlib import Path

import responses
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg.utils.plus import gql

ensure_dagster_dg_tests_import()

from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


@responses.activate
def test_pull_env_command_no_auth(monkeypatch):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        tempfile.TemporaryDirectory() as cloud_config_dir,
    ):
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))
        result = runner.invoke("plus", "env", "pull")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert (
            "`dg plus env pull` requires authentication with Dagster Plus. Run `dg plus login` to authenticate."
            in str(result.output)
        )


@responses.activate
def test_pull_env_command_auth_err(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.SECRETS_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "__typename": "UnauthorizedError",
                        "message": "Not authorized",
                    }
                }
            },
            expected_variables={"onlyViewable": True, "scopes": {"localDeploymentScope": True}},
        )
        result = runner.invoke("plus", "env", "pull")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert "Unauthorized: Not authorized" in str(result.output)


@responses.activate
def test_pull_env_command_python_err(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.SECRETS_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "__typename": "PythonError",
                        "message": "An error has occurred",
                        "stack": "Stack trace",
                    }
                }
            },
            expected_variables={"onlyViewable": True, "scopes": {"localDeploymentScope": True}},
        )
        result = runner.invoke("plus", "env", "pull")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert "Error: An error has occurred" in str(result.output)


@responses.activate
def test_pull_env_command_project(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.SECRETS_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo-bar"],
                                "localDeploymentScope": True,
                            },
                            {
                                "secretName": "BAZ",
                                "secretValue": "qux",
                                "locationNames": [],
                                "localDeploymentScope": True,
                            },
                            {
                                "secretName": "ABC",
                                "secretValue": "def",
                                "locationNames": [],
                                "localDeploymentScope": False,
                            },
                            {
                                "secretName": "QWER",
                                "secretValue": "asdf",
                                "locationNames": ["other"],
                                "localDeploymentScope": True,
                            },
                        ]
                    }
                }
            },
            expected_variables={"onlyViewable": True, "scopes": {"localDeploymentScope": True}},
        )
        result = runner.invoke("plus", "env", "pull")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert result.output.strip() == "Environment variables saved to .env"

        assert Path(".env").read_text().strip() == "FOO=bar\nBAZ=qux"


@responses.activate
def test_pull_env_command_workspace(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        runner.invoke("scaffold", "project", "foo")
        runner.invoke("scaffold", "project", "bar")
        runner.invoke("scaffold", "project", "baz")

        mock_gql_response(
            query=gql.SECRETS_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo"],
                                "localDeploymentScope": True,
                            },
                            {
                                "secretName": "BAZ",
                                "secretValue": "qux",
                                "locationNames": ["foo", "bar"],
                                "localDeploymentScope": True,
                            },
                            {
                                "secretName": "ABC",
                                "secretValue": "def",
                                "locationNames": [],
                                "localDeploymentScope": False,
                            },
                            {
                                "secretName": "QWER",
                                "secretValue": "asdf",
                                "locationNames": ["other"],
                                "localDeploymentScope": True,
                            },
                        ]
                    }
                }
            },
            expected_variables={"onlyViewable": True, "scopes": {"localDeploymentScope": True}},
        )
        result = runner.invoke("plus", "env", "pull")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert (
            result.output.strip()
            == "Environment variables saved to .env for projects in workspace\nEnvironment variables not found for projects: baz"
        )

        assert (Path("foo") / ".env").read_text().strip() == "FOO=bar\nBAZ=qux"
        assert (Path("bar") / ".env").read_text().strip() == "BAZ=qux"
