import os
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

import responses
from dagster_dg.utils import ensure_dagster_dg_tests_import
from dagster_dg.utils.plus import gql
from pytest_httpserver import HTTPServer
from werkzeug import Request, Response

from dagster._utils.env import environ
from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    MASK_JAFFLE_PLATFORM,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    run_command_and_snippet_output,
)

ensure_dagster_dg_tests_import()
from dagster_dg_tests.cli_tests.plus_tests.utils import mock_gql_response, responses

MASK_VENV = (r"Using.*\.venv.*", "")


SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "using-env"
)
import json

gql_matchers: list[tuple[Callable[[Request], bool], dict[str, Any]]] = []


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


def mock_gql_response(
    query: str,
    json_data: dict[str, Any],
) -> None:
    def match(request: Request) -> bool:
        json_body = request.json or {}
        print(json_body)
        body_query_first_line_normalized = (
            json_body["query"].strip().split("\n")[0].strip()
        )
        query_first_line_normalized = query.strip().split("\n")[0].strip()
        print(body_query_first_line_normalized, query_first_line_normalized)
        return True
        return body_query_first_line_normalized == query_first_line_normalized

    gql_matchers.append((match, json_data))


@responses.activate
def test_component_docs_using_env(
    update_snippets: bool, httpserver: HTTPServer
) -> None:
    with isolated_snippet_generation_environment() as get_next_snip_number:
        _run_command(
            cmd="dg scaffold project jaffle-platform --use-editable-dagster && cd jaffle-platform",
        )
        _run_command(cmd="uv venv")
        _run_command(cmd="uv sync")
        _run_command(
            f"uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster'!s}' '{DAGSTER_ROOT / 'python_modules' / 'dagster-webserver'!s}'"
        )

        # Set up dbt
        run_command_and_snippet_output(
            cmd="git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git dbt && rm -rf dbt/.git",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-jaffle-clone.txt",
            update_snippets=update_snippets,
            ignore_output=True,
        )
        _run_command(
            f"uv add --editable '{EDITABLE_DIR / 'dagster-dbt'!s}' && uv add --editable '{EDITABLE_DIR / 'dagster-components'!s}[dbt]'; uv add dbt-duckdb"
        )
        run_command_and_snippet_output(
            cmd="dg list component-type",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-list-component-types.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
        )

        # Scaffold dbt project components
        run_command_and_snippet_output(
            cmd="dg scaffold dagster_components.dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-scaffold-jdbt.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[MASK_JAFFLE_PLATFORM],
        )
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
            ],
        )
        create_file(
            Path("jaffle_platform") / "defs" / "jdbt" / "component.yaml",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-project-jdbt.yaml",
            contents=format_multiline("""
                type: dagster_components.dagster_dbt.DbtProjectComponent

                attributes:
                  dbt:
                    project_dir: ../../../dbt/jdbt
                  asset_attributes:
                    key: "jaffle_platform/{{ env('DBT_SCHEMA') }}/{{ node.name }}"
            """),
        )
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
            ],
            expect_error=True,
        )
        run_command_and_snippet_output(
            cmd="dg check yaml --fix-env-requirements",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
            ],
            expect_error=True,
        )
        run_command_and_snippet_output(
            cmd="echo 'DBT_SCHEMA=jaffle_shop' >> .env",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
            snippet_replace_regex=[
                MASK_JAFFLE_PLATFORM,
            ],
        )
        run_command_and_snippet_output(
            cmd="dg check yaml",
            snippet_path=SNIPPETS_DIR
            / f"{get_next_snip_number()}-dg-component-check.txt",
            update_snippets=update_snippets,
        )
        run_command_and_snippet_output(
            cmd="dg env list",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-list.txt",
            update_snippets=update_snippets,
        )

        mock_gql_mutation(
            gql.GET_SECRETS_FOR_SCOPES_QUERY,
            json_data={
                "data": {
                    "secretsForScopes": {
                        "secrets": [
                            {
                                "secretName": "DBT_SCHEMA",
                                "locationNames": ["jaffle-platform"],
                                "fullDeploymentScope": False,
                                "allBranchDeploymentsScope": True,
                                "localDeploymentScope": True,
                            }
                        ]
                    }
                }
            },
            expected_variables={
                "locationName": "jaffle-platform",
                "scopes": {
                    "fullDeploymentScope": True,
                    "allBranchDeploymentsScope": True,
                    "localDeploymentScope": True,
                },
                "secretName": "DBT_SCHEMA",
            },
        )

        def _handle(request: Request) -> Response:
            for match, data in gql_matchers:
                if match(request):
                    return Response(json.dumps(data), status=200)
            return Response(
                json.dumps({}),
                status=200,
            )

        httpserver.expect_request("/hooli/graphql").respond_with_handler(_handle)

        Path(os.environ["DG_CLI_CONFIG"]).write_text(
            f"""
            [cli.telemetry]
            enabled = false
            [cli.plus]
            organization = "hooli"
            url = "{httpserver.url_for('').rstrip('/')}"
            user_token = "test"
            default_deployment = "test"
            """
        )

        run_command_and_snippet_output(
            cmd="dg env list",
            snippet_path=SNIPPETS_DIR / f"{get_next_snip_number()}-dg-env-list.txt",
            update_snippets=update_snippets,
        )
