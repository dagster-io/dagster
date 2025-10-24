import tempfile
from pathlib import Path

import pytest
import responses
from dagster_dg_cli.utils.plus import gql
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
    set_env_var,
)

from dagster_dg_cli_tests.cli_tests.plus_tests.utils import mock_gql_response

########################################################
# PULL ENV COMMAND
########################################################


@responses.activate
def test_pull_env_command_no_auth(monkeypatch):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        tempfile.TemporaryDirectory() as cloud_config_dir,
    ):
        monkeypatch.setenv("DG_CLI_CONFIG", str(Path(cloud_config_dir) / "dg.toml"))
        monkeypatch.setenv("DAGSTER_CLOUD_CLI_CONFIG", str(Path(cloud_config_dir) / "config"))
        result = runner.invoke("plus", "pull", "env")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert (
            "`dg plus` commands require authentication with Dagster Plus. Run `dg plus login` to authenticate."
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
        result = runner.invoke("plus", "pull", "env")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert "Error: Not authorized" in str(result.output)


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
        result = runner.invoke("plus", "pull", "env")
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
        result = runner.invoke("plus", "pull", "env")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert result.output.strip() == "Environment variables saved to .env"

        assert Path(".env").read_text().strip() == "FOO=bar\nBAZ=qux"


@responses.activate
def test_pull_env_command_workspace(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        runner.invoke_create_dagster("project", "--no-uv-sync", "foo")
        runner.invoke_create_dagster("project", "--no-uv-sync", "bar")
        runner.invoke_create_dagster("project", "--no-uv-sync", "baz")

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
        result = runner.invoke("plus", "pull", "env")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert (
            result.output.strip()
            == "Environment variables saved to .env for projects in workspace\nEnvironment variables not found for projects: baz"
        )

        assert (Path("foo") / ".env").read_text().strip() == "FOO=bar\nBAZ=qux"
        assert (Path("bar") / ".env").read_text().strip() == "BAZ=qux"


########################################################
# ADD ENV COMMAND, WORKSPACE LEVEL
########################################################


def test_add_env_command_no_value_workspace(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        result = runner.invoke("plus", "create", "env", "FOO")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert "Environment variable value is required" in str(result.output)


@pytest.mark.parametrize("input_type", ["direct", "from-local-env"])
@responses.activate
def test_add_env_command_basic_success_workspace(dg_plus_cli_config, input_type: str):
    expected_secret_value = (
        "bar" if input_type == "direct" else ("baz" if input_type == "from-local-env" else "qux")
    )
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
        set_env_var("FOO", "baz"),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={"data": {"secretsOrError": {"secrets": []}}},
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": expected_secret_value,
                            "locationNames": [],
                        }
                    }
                }
            },
            expected_variables={
                "secretName": "FOO",
                "secretValue": expected_secret_value,
                "scopes": {
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                    "localDeploymentScope": True,
                },
                "locationName": None,
            },
        )

        input_args = ["bar"] if input_type == "direct" else ["--from-local-env"]
        result = runner.invoke("plus", "create", "env", "FOO", *input_args)
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        additional_output = ""
        if input_type == "from-local-env":
            additional_output = "Reading environment variable FOO from shell environment\n\n"
        assert (
            result.output.strip()
            == f"{additional_output}Environment variable FOO set in branch, full, local scope for all locations in deployment hooli-dev"
        )


@pytest.mark.parametrize(
    "scopes",
    [
        ["branch"],
        ["full"],
        ["local"],
        ["branch", "full"],
        ["branch", "local"],
        ["full", "local"],
        ["branch", "full", "local"],
    ],
)
@responses.activate
def test_add_env_command_scopes_workspace(dg_plus_cli_config, scopes: list[str]):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
        set_env_var("FOO", "baz"),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={"data": {"secretsOrError": {"secrets": []}}},
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": [],
                        }
                    }
                }
            },
            expected_variables={
                "secretName": "FOO",
                "secretValue": "bar",
                "scopes": {
                    "fullDeploymentScope": "full" in scopes,
                    "allBranchDeploymentsScope": "branch" in scopes,
                    "localDeploymentScope": "local" in scopes,
                },
                "locationName": None,
            },
        )

        scope_args = []
        for scope in scopes:
            scope_args.append("--scope")
            scope_args.append(scope)
        result = runner.invoke("plus", "create", "env", "FOO", "bar", *scope_args)
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert (
            result.output.strip()
            == f"Environment variable FOO set in {', '.join(scopes)} scope for all locations in deployment hooli-dev"
        )


@pytest.mark.parametrize("accept", [True, False])
@responses.activate
def test_add_env_command_warn_if_existing_workspace(dg_plus_cli_config, accept: bool):
    # Test that we warn and ask for confirmation if we are going to update any existing env vars
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_workspace(runner),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": [],
                                "fullDeploymentScope": False,
                                "allBranchDeploymentsScope": False,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": None,
                        }
                    }
                }
            },
        )
        result = runner.invoke(
            "plus", "create", "env", "FOO", "bar", input="y\n" if accept else "n\n"
        )
        assert result.exit_code == 0 if accept else 1, result.output + " " + str(result.exception)
        if accept:
            assert (
                result.output.strip()
                == "Environment variable FOO is already configured for local scope.\n\n"
                "Are you sure you want to update environment variable FOO in branch, full, local scope for all locations? [y/N]: y\n\n"
                "Environment variable FOO set in branch, full, local scope for all locations in deployment hooli-dev"
            )


########################################################
# ADD ENV COMMAND
########################################################


def test_add_env_command_no_value(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("plus", "create", "env", "FOO")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert "Environment variable value is required" in str(result.output)


@pytest.mark.parametrize("input_type", ["direct", "from-local-env", "from-env-file"])
@responses.activate
def test_add_env_command_basic_success(dg_plus_cli_config, input_type: str):
    expected_secret_value = (
        "bar" if input_type == "direct" else ("baz" if input_type == "from-local-env" else "qux")
    )
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        set_env_var("FOO", "baz"),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={"data": {"secretsOrError": {"secrets": []}}},
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": expected_secret_value,
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
            expected_variables={
                "secretName": "FOO",
                "secretValue": expected_secret_value,
                "scopes": {
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                    "localDeploymentScope": True,
                },
                "locationName": "foo-bar",
            },
        )

        input_args = ["bar"] if input_type == "direct" else ["--from-local-env"]
        if input_type == "from-env-file":
            Path(".env").write_text("FOO=qux")
        result = runner.invoke("plus", "create", "env", "FOO", *input_args)
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        additional_output = ""
        if input_type == "from-env-file":
            additional_output = "Reading environment variable FOO from project .env file\n\n"
        elif input_type == "from-local-env":
            additional_output = "Reading environment variable FOO from shell environment\n\n"
        assert (
            result.output.strip()
            == f"{additional_output}Environment variable FOO set in branch, full, local scope for location foo-bar in deployment hooli-dev"
        )


@pytest.mark.parametrize(
    "scopes",
    [
        ["branch"],
        ["full"],
        ["local"],
        ["branch", "full"],
        ["branch", "local"],
        ["full", "local"],
        ["branch", "full", "local"],
    ],
)
@responses.activate
def test_add_env_command_scopes(dg_plus_cli_config, scopes: list[str]):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
        set_env_var("FOO", "baz"),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={"data": {"secretsOrError": {"secrets": []}}},
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
            expected_variables={
                "secretName": "FOO",
                "secretValue": "bar",
                "scopes": {
                    "fullDeploymentScope": "full" in scopes,
                    "allBranchDeploymentsScope": "branch" in scopes,
                    "localDeploymentScope": "local" in scopes,
                },
                "locationName": "foo-bar",
            },
        )

        scope_args = []
        for scope in scopes:
            scope_args.append("--scope")
            scope_args.append(scope)
        result = runner.invoke("plus", "create", "env", "FOO", "bar", *scope_args)
        assert result.exit_code == 0, result.output + " " + str(result.exception)

        assert (
            result.output.strip()
            == f"Environment variable FOO set in {', '.join(scopes)} scope for location foo-bar in deployment hooli-dev"
        )


@responses.activate
def test_add_env_command_basic_success_global(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        # Existing non-global secret, which we ignore
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo-bar"],
                                "fullDeploymentScope": True,
                                "allBranchDeploymentsScope": True,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": [],
                        }
                    }
                }
            },
            expected_variables={
                "secretName": "FOO",
                "secretValue": "bar",
                "scopes": {
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                    "localDeploymentScope": True,
                },
                "locationName": None,
            },
        )
        result = runner.invoke("plus", "create", "env", "FOO", "bar", "--global")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert (
            result.output.strip()
            == "Environment variable FOO set in branch, full, local scope for all locations in deployment hooli-dev"
        )


@pytest.mark.parametrize("accept", [True, False])
@responses.activate
def test_add_env_command_warn_if_global(dg_plus_cli_config, accept: bool):
    # Test that we warn and ask for confirmation if a global copy of the env var already exists
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": [],
                                "fullDeploymentScope": True,
                                "allBranchDeploymentsScope": True,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
        )
        result = runner.invoke(
            "plus", "create", "env", "FOO", "bar", input="y\n" if accept else "n\n"
        )
        assert result.exit_code == 0 if accept else 1, result.output + " " + str(result.exception)
        if accept:
            assert (
                result.output.strip()
                == "Environment variable FOO is set globally within the current deployment. The current command will only update the value for location foo-bar. Use --global to update this value for all locations.\n\n"
                "Are you sure you want to update environment variable FOO in branch, full, local scope for location foo-bar? [y/N]: y\n\n"
                "Environment variable FOO set in branch, full, local scope for location foo-bar in deployment hooli-dev"
            )


@responses.activate
def test_add_env_command_exception_if_multiple_locations(dg_plus_cli_config):
    # We currently don't support updating env vars which are set in multiple locations (but not at the deployment level),
    # since this gets into a permissions minefield.
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo-bar", "other"],
                                "fullDeploymentScope": True,
                                "allBranchDeploymentsScope": True,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
        )
        result = runner.invoke("plus", "create", "env", "FOO", "bar")
        assert result.exit_code != 0, result.output + " " + str(result.exception)
        assert (
            result.output.strip()
            == "Error: Environment variable FOO is configured for multiple locations foo-bar, other, and cannot be modified via the CLI."
        )


@pytest.mark.parametrize("accept", [True, False])
@responses.activate
def test_add_env_command_warn_if_existing(dg_plus_cli_config, accept: bool):
    # Test that we warn and ask for confirmation if we are going to update any existing env vars
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo-bar"],
                                "fullDeploymentScope": False,
                                "allBranchDeploymentsScope": False,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
        )
        result = runner.invoke(
            "plus", "create", "env", "FOO", "bar", input="y\n" if accept else "n\n"
        )
        assert result.exit_code == 0 if accept else 1, result.output + " " + str(result.exception)
        if accept:
            assert (
                result.output.strip()
                == "Environment variable FOO is already configured for local scope for location foo-bar.\n\n"
                "Are you sure you want to update environment variable FOO in branch, full, local scope for location foo-bar? [y/N]: y\n\n"
                "Environment variable FOO set in branch, full, local scope for location foo-bar in deployment hooli-dev"
            )


@responses.activate
def test_add_env_command_no_confirm(dg_plus_cli_config):
    # Test that we warn and ask for confirmation if we are going to update any existing env vars
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "secretValue": "bar",
                                "locationNames": ["foo-bar"],
                                "fullDeploymentScope": False,
                                "allBranchDeploymentsScope": False,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
        )
        mock_gql_response(
            query=gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
            json_data={
                "data": {
                    "createOrUpdateSecretForScopes": {
                        "secret": {
                            "secretName": "FOO",
                            "secretValue": "bar",
                            "locationNames": ["foo-bar"],
                        }
                    }
                }
            },
        )
        result = runner.invoke("plus", "create", "env", "FOO", "bar", "--yes")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert (
            result.output.strip()
            == "Environment variable FOO is already configured for local scope for location foo-bar.\n\n"
            "Environment variable FOO set in branch, full, local scope for location foo-bar in deployment hooli-dev"
        )
