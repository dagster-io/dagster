# ruff: noqa: I001 - import order differs between CI and local due to package installation differences
import textwrap
from pathlib import Path

import responses
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
    match_terminal_box_output,
)

from dagster_dg_cli.utils.plus import gql
from dagster_dg_cli_tests.cli_tests.plus_tests.utils import mock_gql_response

# ###############################################################
# ##### TEST LIST COMMANDS WITH PLUS CONFIGURED ENV VARS
# ###############################################################


@responses.activate
def test_list_env_succeeds(dg_plus_cli_config):
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            No environment variables are defined for this project.
        """).strip()
        )

        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
            json_data={"data": {"secretsOrError": {"secrets": []}}},
            expected_variables={
                "scopes": {
                    "localDeploymentScope": True,
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                },
                "locationName": "foo-bar",
            },
        )
        Path(".env").write_text("FOO=bar")
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert match_terminal_box_output(
            result.output.strip(),
            textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━┳━━━━━━━━┳━━━━━━┓
               ┃ Env Var ┃ Value ┃ Components ┃ Dev ┃ Branch ┃ Full ┃
               ┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━╇━━━━━━━━╇━━━━━━┩
               │ FOO     │ ✓     │            │     │        │      │
               └─────────┴───────┴────────────┴─────┴────────┴──────┘
            """).strip(),
        )

        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "locationNames": ["foo-bar"],
                                "localDeploymentScope": True,
                                "fullDeploymentScope": True,
                                "allBranchDeploymentsScope": False,
                            },
                        ]
                    }
                }
            },
            expected_variables={
                "scopes": {
                    "localDeploymentScope": True,
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                },
                "locationName": "foo-bar",
            },
        )
        Path(".env").write_text("FOO=bar")
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert match_terminal_box_output(
            result.output.strip(),
            textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━┳━━━━━━━━┳━━━━━━┓
               ┃ Env Var ┃ Value ┃ Components ┃ Dev ┃ Branch ┃ Full ┃
               ┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━╇━━━━━━━━╇━━━━━━┩
               │ FOO     │ ✓     │            │ ✓   │        │ ✓    │
               └─────────┴───────┴────────────┴─────┴────────┴──────┘
            """).strip(),
        )

        result = runner.invoke(
            "scaffold",
            "defs",
            "dagster_test.components.AllMetadataEmptyComponent",
            "subfolder/mydefs",
        )
        assert_runner_result(result)
        Path("src/foo_bar/defs/subfolder/mydefs/defs.yaml").write_text(
            textwrap.dedent("""
                type: dagster_test.components.AllMetadataEmptyComponent

                requirements:
                    env:
                        - BAZ
            """)
        )

        mock_gql_response(
            query=gql.GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
            json_data={
                "data": {
                    "secretsOrError": {
                        "secrets": [
                            {
                                "secretName": "FOO",
                                "locationNames": ["foo-bar"],
                                "localDeploymentScope": True,
                                "fullDeploymentScope": True,
                                "allBranchDeploymentsScope": False,
                            },
                            {
                                "secretName": "BAZ",
                                "locationNames": [],
                                "localDeploymentScope": True,
                                "fullDeploymentScope": False,
                                "allBranchDeploymentsScope": False,
                            },
                        ]
                    }
                }
            },
            expected_variables={
                "scopes": {
                    "localDeploymentScope": True,
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                },
                "locationName": "foo-bar",
            },
        )
        Path(".env").write_text("FOO=bar")
        result = runner.invoke("list", "env")
        assert_runner_result(result)
        assert match_terminal_box_output(
            result.output.strip(),
            textwrap.dedent("""
               ┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━┳━━━━━━┓
               ┃ Env Var ┃ Value ┃ Components       ┃ Dev ┃ Branch ┃ Full ┃
               ┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━╇━━━━━━┩
               │ BAZ     │       │ subfolder/mydefs │ ✓   │        │      │
               │ FOO     │ ✓     │                  │ ✓   │        │ ✓    │
               └─────────┴───────┴──────────────────┴─────┴────────┴──────┘
            """).strip(),
        )
