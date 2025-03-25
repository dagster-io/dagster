from pathlib import Path

import responses
from dagster_dg.utils.plus import gql
from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response
from dagster_dg_tests.utils import ProxyRunner, isolated_example_project_foo_bar


@responses.activate
def test_pull_env_command(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        mock_gql_response(
            query=gql.LOCAL_SECRETS_FILE_QUERY,
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
        )
        result = runner.invoke("env", "pull")
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert result.output.strip() == "Environment variables saved to .env"

        assert Path(".env").read_text().strip() == "FOO=bar\nBAZ=qux"
