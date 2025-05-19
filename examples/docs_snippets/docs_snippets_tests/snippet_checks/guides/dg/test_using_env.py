import json
import os
import textwrap
from contextlib import ExitStack
from enum import Enum
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
import responses
from dagster_dg.cli.utils import activate_venv
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg.utils.plus import gql
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_EDITABLE_DAGSTER,
    format_multiline,
    isolated_snippet_generation_environment,
    make_project_path_mask,
)
from docs_snippets_tests.snippet_checks.utils import (
    create_file,
    run_command_and_snippet_output,
)

ensure_dagster_dg_tests_import()
from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response, responses

MASK_VENV = (r"Using.*\.venv.*", "")
REMOVE_EXCESS_DESCRIPTION_ROW = (r"\n│\s+│\s+│\s+│\s+│.*│\n", "\n")
MASK_INGESTION = make_project_path_mask("ingestion")
SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "using-env"
)

# Keep a global list of graphql query/mutation matchers, which are used to mock responses
# from the Dagster Plus GraphQL API.
gql_matchers: list[tuple[Callable[[Request], bool], dict[str, Any]]] = []

# For some reason dagster-evidence is producing this in the output:
#
#    <blank line>
#        warnings.warn(message)
#
# Mask this until we figure out how to get rid of it.
_MASK_EMPTY_WARNINGS = (r"\n +warnings.warn\(message\)\n", "")


@pytest.fixture
def mock_graphql_server(httpserver: HTTPServer) -> str:
    def _handle(request: Request) -> Response:
        for match, data in reversed(gql_matchers):
            if match(request):
                return Response(json.dumps(data), status=200)
        return Response(
            json.dumps({}),
            status=200,
        )

    httpserver.expect_request("/hooli/graphql").respond_with_handler(_handle)

    return httpserver.url_for("").rstrip("/")


def mock_gql_mutation(
    mutation: str,
    json_data: dict[str, Any],
    expected_variables: Optional[dict[str, Any]] = None,
) -> None:
    def match(request: Request) -> bool:
        json_body = request.json or {}
        body_query_first_line_normalized = (
            json_body["query"].strip().split("\n")[0].strip()
        )
        query_first_line_normalized = mutation.strip().split("\n")[0].strip()
        if expected_variables and json_body["variables"] != expected_variables:
            return False
        return body_query_first_line_normalized == query_first_line_normalized

    gql_matchers.append((match, json_data))


class EnvVarScope(Enum):
    LOCAL = "localDeploymentScope"
    BRANCH = "allBranchDeploymentsScope"
    FULL = "fullDeploymentScope"


def mock_gql_for_list_env(
    location_name: str,
    secrets: dict[str, set[EnvVarScope]],
) -> None:
    scope_vars_by_name = {
        name: {
            "fullDeploymentScope": False,
            "allBranchDeploymentsScope": False,
            "localDeploymentScope": False,
            **{scope.value: True for scope in scopes},
        }
        for name, scopes in secrets.items()
    }
    mock_gql_mutation(
        gql.GET_SECRETS_FOR_SCOPES_QUERY_NO_VALUE,
        json_data={
            "data": {
                "secretsOrError": {
                    "secrets": [
                        {
                            "secretName": name,
                            "locationNames": [location_name],
                            **scope_vars,
                        }
                        for name, scope_vars in scope_vars_by_name.items()
                    ]
                }
            }
        },
        expected_variables={
            "locationName": location_name,
            "scopes": {
                "fullDeploymentScope": True,
                "allBranchDeploymentsScope": True,
                "localDeploymentScope": True,
            },
        },
    )


def mock_gql_for_pull_env(
    location_name: str,
    secrets: dict[str, set[EnvVarScope]],
) -> None:
    scope_vars_by_name = {
        name: {
            "fullDeploymentScope": False,
            "allBranchDeploymentsScope": False,
            "localDeploymentScope": False,
            **{scope.value: True for scope in scopes},
        }
        for name, scopes in secrets.items()
    }
    mock_gql_mutation(
        gql.SECRETS_QUERY,
        json_data={
            "data": {
                "secretsOrError": {
                    "secrets": [
                        {
                            "secretName": name,
                            "locationNames": [location_name],
                            "secretValue": "...",
                            **scope_vars,
                        }
                        for name, scope_vars in scope_vars_by_name.items()
                    ]
                }
            }
        },
        expected_variables={
            "onlyViewable": True,
            "scopes": {
                "localDeploymentScope": True,
            },
        },
    )


def mock_gql_for_create_env(
    location_name: str, secret_name: str, secret_value: str, scopes: set[EnvVarScope]
) -> None:
    scope_vars = {
        "fullDeploymentScope": False,
        "allBranchDeploymentsScope": False,
        "localDeploymentScope": False,
        **{scope.value: True for scope in scopes},
    }
    mock_gql_mutation(
        gql.GET_SECRETS_FOR_SCOPES_QUERY,
        json_data={"data": {"secretsOrError": {"secrets": []}}},
        expected_variables={
            "locationName": location_name,
            "scopes": scope_vars,
            "secretName": secret_name,
        },
    )
    mock_gql_mutation(
        gql.CREATE_OR_UPDATE_SECRET_FOR_SCOPES_MUTATION,
        json_data={
            "data": {
                "createOrUpdateSecretForScopes": {
                    "secret": {
                        "secretName": secret_name,
                        "locationNames": [location_name],
                        **scope_vars,
                    }
                }
            }
        },
        expected_variables={
            "locationName": location_name,
            "scopes": scope_vars,
            "secretName": secret_name,
            "secretValue": secret_value,
        },
    )


@responses.activate
def test_component_docs_using_env(
    update_snippets: bool, mock_graphql_server: str
) -> None:
    with (
        isolated_snippet_generation_environment() as get_next_snip_number,
        ExitStack() as stack,
    ):
        run_command_and_snippet_output(
            cmd="dg scaffold project ingestion",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-init.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_EDITABLE_DAGSTER,
                MASK_INGESTION,
                (r"Using CPython.*?(?:\n(?!\n).*)*\n\n", "...venv creation...\n"),
                # Kind of a hack, this appears after you enter "y" at the prompt, but when
                # we simulate the input we don't get the newline we get in terminal so we
                # slide it in here.
                (r"Running `uv sync`\.\.\.", "\nRunning `uv sync`..."),
            ],
            input_str="y\n",
            ignore_output=True,
        )
        run_command_and_snippet_output(
            cmd="cd ingestion && source .venv/bin/activate",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-activate-venv.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )
        # Activate the virtual environment after creating it-- executing the above `source
        # .venv/bin/activate` command does not actually activate the virtual environment
        # across subsequent command invocations in this test.
        stack.enter_context(activate_venv(".venv"))

        run_command_and_snippet_output(
            cmd=f"uv add --editable '{EDITABLE_DIR / 'dagster-sling'!s}'",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-uv-add-sling.txt",
            update_snippets=update_snippets,
            ignore_output=True,
            print_cmd="uv add dagster-sling",
        )
        run_command_and_snippet_output(
            cmd="dg list plugins",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_INGESTION, _MASK_EMPTY_WARNINGS],
        )

        # Scaffold dbt project components
        run_command_and_snippet_output(
            cmd="dg scaffold dagster_sling.SlingReplicationCollectionComponent ingest_to_snowflake",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-scaffold-sling.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_INGESTION, _MASK_EMPTY_WARNINGS],
        )

        run_command_and_snippet_output(
            cmd=textwrap.dedent("""
                    curl -O https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv
                """).strip(),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-curl.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )

        create_file(
            file_path=Path("src")
            / "ingestion"
            / "defs"
            / "ingest_files"
            / "replication.yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-replication.yaml",
            contents=textwrap.dedent(
                """
                    source: LOCAL
                    target: SNOWFLAKE

                    defaults:
                      mode: full-refresh
                      object: "{stream_table}"

                    streams:
                      file://raw_customers.csv:
                        object: "sandbox.raw_customers"
                """,
            ).strip(),
        )

        # Add Snowflake connection
        create_file(
            file_path=Path("src")
            / "ingestion"
            / "defs"
            / "ingest_files"
            / "component.yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-component.yaml",
            contents=format_multiline("""
                type: dagster_sling.SlingReplicationCollectionComponent

                attributes:
                  sling:
                    connections:
                      - name: SNOWFLAKE
                        type: snowflake
                        account: "{{ env('SNOWFLAKE_ACCOUNT') }}"
                        user: "{{ env('SNOWFLAKE_USER') }}"
                        password: "{{ env('SNOWFLAKE_PASSWORD') }}"
                        database: "{{ env('SNOWFLAKE_DATABASE') }}"
                    replications:
                      - path: replication.yaml
                """),
        )

        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_INGESTION,
            ],
            expect_error=True,
        )

        # Add Snowflake connection
        create_file(
            file_path=Path("src")
            / "ingestion"
            / "defs"
            / "ingest_files"
            / "component.yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-component-with-env-deps.yaml",
            contents=format_multiline("""
                type: dagster_sling.SlingReplicationCollectionComponent

                attributes:
                  sling:
                    connections:
                      - name: SNOWFLAKE
                        type: snowflake
                        account: "{{ env('SNOWFLAKE_ACCOUNT') }}"
                        user: "{{ env('SNOWFLAKE_USER') }}"
                        password: "{{ env('SNOWFLAKE_PASSWORD') }}"
                        database: "{{ env('SNOWFLAKE_DATABASE') }}"
                    replications:
                      - path: replication.yaml

                requirements:
                  env:
                    - SNOWFLAKE_ACCOUNT
                    - SNOWFLAKE_USER
                    - SNOWFLAKE_PASSWORD
                    - SNOWFLAKE_DATABASE
                """),
        )

        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check-fixed.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_INGESTION,
            ],
        )

        run_command_and_snippet_output(
            cmd="dg list env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-list-env.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_INGESTION, REMOVE_EXCESS_DESCRIPTION_ROW],
        )
        run_command_and_snippet_output(
            cmd=textwrap.dedent("""
                echo 'SNOWFLAKE_ACCOUNT=...' >> .env
                echo 'SNOWFLAKE_USER=...' >> .env
                echo 'SNOWFLAKE_PASSWORD=...' >> .env
                echo "SNOWFLAKE_DATABASE=sandbox" >> .env
            """).strip(),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-inject-env.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_INGESTION,
            ],
        )

        run_command_and_snippet_output(
            cmd="dg list env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-list-env.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_INGESTION, REMOVE_EXCESS_DESCRIPTION_ROW],
        )

        Path(os.environ["DG_CLI_CONFIG"]).write_text(
            f"""
            [cli.telemetry]
            enabled = false
            [cli.plus]
            organization = "hooli"
            url = "{mock_graphql_server}"
            user_token = "test"
            default_deployment = "prod"
            """
        )

        mock_gql_for_list_env(
            location_name="ingestion",
            secrets={},
        )
        run_command_and_snippet_output(
            cmd="dg list env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-list.txt",
            update_snippets=update_snippets,
        )

        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_ACCOUNT",
            secret_value="...",
            scopes={EnvVarScope.LOCAL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_USER",
            secret_value="...",
            scopes={EnvVarScope.LOCAL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_PASSWORD",
            secret_value="...",
            scopes={EnvVarScope.LOCAL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_DATABASE",
            secret_value="sandbox",
            scopes={EnvVarScope.LOCAL},
        )
        run_command_and_snippet_output(
            cmd=textwrap.dedent("""
                dg plus create env SNOWFLAKE_ACCOUNT --from-local-env --scope local &&
                dg plus create env SNOWFLAKE_USER --from-local-env --scope local &&
                dg plus create env SNOWFLAKE_PASSWORD --from-local-env --scope local &&
                dg plus create env SNOWFLAKE_DATABASE --from-local-env --scope local
            """).strip(),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-plus-env-add.txt",
            update_snippets=update_snippets,
        )

        mock_gql_for_list_env(
            location_name="ingestion",
            secrets={
                "SNOWFLAKE_USER": {EnvVarScope.LOCAL},
                "SNOWFLAKE_PASSWORD": {EnvVarScope.LOCAL},
                "SNOWFLAKE_DATABASE": {EnvVarScope.LOCAL},
                "SNOWFLAKE_ACCOUNT": {EnvVarScope.LOCAL},
            },
        )
        run_command_and_snippet_output(
            cmd="dg list env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-list.txt",
            update_snippets=update_snippets,
        )

        mock_gql_for_pull_env(
            location_name="ingestion",
            secrets={
                "SNOWFLAKE_USER": {EnvVarScope.LOCAL},
                "SNOWFLAKE_PASSWORD": {EnvVarScope.LOCAL},
                "SNOWFLAKE_DATABASE": {EnvVarScope.LOCAL},
                "SNOWFLAKE_ACCOUNT": {EnvVarScope.LOCAL},
            },
        )
        run_command_and_snippet_output(
            cmd="dg plus pull env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-pull.txt",
            update_snippets=update_snippets,
        )

        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_ACCOUNT",
            secret_value="...",
            scopes={EnvVarScope.BRANCH, EnvVarScope.FULL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_USER",
            secret_value="...",
            scopes={EnvVarScope.BRANCH, EnvVarScope.FULL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_PASSWORD",
            secret_value="...",
            scopes={EnvVarScope.BRANCH, EnvVarScope.FULL},
        )
        mock_gql_for_create_env(
            location_name="ingestion",
            secret_name="SNOWFLAKE_DATABASE",
            secret_value="production",
            scopes={EnvVarScope.BRANCH, EnvVarScope.FULL},
        )
        run_command_and_snippet_output(
            cmd=textwrap.dedent("""
                dg plus create env SNOWFLAKE_ACCOUNT ... --scope branch --scope full &&
                dg plus create env SNOWFLAKE_USER ... --scope branch --scope full &&
                dg plus create env SNOWFLAKE_PASSWORD ... --scope branch --scope full &&
                dg plus create env SNOWFLAKE_DATABASE production --scope branch --scope full
            """).strip(),
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-plus-env-add.txt",
            update_snippets=update_snippets,
        )

        mock_gql_for_list_env(
            location_name="ingestion",
            secrets={
                "SNOWFLAKE_USER": {
                    EnvVarScope.LOCAL,
                    EnvVarScope.BRANCH,
                    EnvVarScope.FULL,
                },
                "SNOWFLAKE_PASSWORD": {
                    EnvVarScope.LOCAL,
                    EnvVarScope.BRANCH,
                    EnvVarScope.FULL,
                },
                "SNOWFLAKE_DATABASE": {
                    EnvVarScope.LOCAL,
                    EnvVarScope.BRANCH,
                    EnvVarScope.FULL,
                },
                "SNOWFLAKE_ACCOUNT": {
                    EnvVarScope.LOCAL,
                    EnvVarScope.BRANCH,
                    EnvVarScope.FULL,
                },
            },
        )
        run_command_and_snippet_output(
            cmd="dg list env",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-list.txt",
            update_snippets=update_snippets,
        )
