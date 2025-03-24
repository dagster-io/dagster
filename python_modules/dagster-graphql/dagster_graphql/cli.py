import asyncio
from collections.abc import Mapping
from io import TextIOWrapper
from typing import Optional
from urllib.parse import urljoin, urlparse

import click
import dagster._check as check
import dagster_shared.seven as seven
import requests
from dagster._cli.utils import (
    assert_no_remaining_opts,
    get_instance_for_cli,
    get_temporary_instance_for_cli,
)
from dagster._cli.workspace.cli_target import (
    WORKSPACE_TARGET_WARNING,
    WorkspaceOpts,
    workspace_options,
)
from dagster._core.workspace.context import WorkspaceProcessContext
from dagster._utils import DEFAULT_WORKSPACE_YAML_FILENAME
from dagster._utils.log import get_stack_trace_array

from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.schema import create_schema
from dagster_graphql.version import __version__


def create_dagster_graphql_cli():
    return ui


def execute_query(
    workspace_process_context: WorkspaceProcessContext,
    query: str,
    variables: Optional[Mapping[str, object]] = None,
):
    check.inst_param(
        workspace_process_context, "workspace_process_context", WorkspaceProcessContext
    )
    check.str_param(query, "query")
    check.opt_mapping_param(variables, "variables")

    query = query.strip("'\" \n\t")

    context = workspace_process_context.create_request_context()

    result = asyncio.run(
        create_schema().execute_async(
            query,
            context_value=context,
            variable_values=variables,
        )
    )

    result_dict = result.formatted

    # Here we detect if this is in fact an error response
    # If so, we iterate over the result_dict and the original result
    # which contains a GraphQLError. If that GraphQL error contains
    # an original_error property (which is the exception the resolver
    # has thrown, typically) we serialize the stack trace of that exception
    # in the 'stack_trace' property of each error to ease debugging

    if "errors" in result_dict:
        result_dict_errors = check.list_elem(result_dict, "errors", of_type=Exception)
        result_errors = check.is_list(result.errors, of_type=Exception)
        check.invariant(len(result_dict_errors) == len(result_errors))
        for python_error, error_dict in zip(result_errors, result_dict_errors):
            # Typing errors caught by making is_list typed -- schrockn 2024-06-09
            if hasattr(python_error, "original_error") and python_error.original_error:  # type: ignore
                error_dict["stack_trace"] = get_stack_trace_array(python_error.original_error)  # type: ignore

    return result_dict


def execute_query_from_cli(workspace_process_context, query, variables=None, output=None):
    check.inst_param(
        workspace_process_context, "workspace_process_context", WorkspaceProcessContext
    )
    check.str_param(query, "query")
    check.opt_str_param(variables, "variables")
    check.opt_str_param(output, "output")

    query = query.strip("'\" \n\t")

    result_dict = execute_query(
        workspace_process_context,
        query,
        variables=seven.json.loads(variables) if variables else None,
    )
    str_res = seven.json.dumps(result_dict)

    # Since this the entry point for CLI execution, some tests depend on us putting the result on
    # stdout
    if output:
        check.str_param(output, "output")
        with open(output, "w", encoding="utf8") as f:
            f.write(str_res + "\n")
    else:
        print(str_res)  # noqa: T201

    return str_res


def execute_query_against_remote(host, query, variables):
    parsed_url = urlparse(host)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise click.UsageError(
            f"Host {host} is not a valid URL. Host URL should include scheme ie http://localhost."
        )

    sanity_check = requests.get(urljoin(host, "/server_info"))
    sanity_check.raise_for_status()
    if "dagster_webserver" not in sanity_check.text:
        raise click.UsageError(
            f"Host {host} failed sanity check. It is not a dagster-webserver instance."
        )
    response = requests.post(
        urljoin(host, "/graphql"),
        # send query and vars as post body to avoid uri length limits
        json={"query": query, "variables": variables},
    )
    response.raise_for_status()
    str_res = response.json()
    return str_res


PREDEFINED_QUERIES = {
    "launchPipelineExecution": LAUNCH_PIPELINE_EXECUTION_MUTATION,
}


@click.command(
    name="ui",
    help=(
        "Run a GraphQL query against the dagster interface to a specified repository or"
        f" pipeline/job.\n\n{WORKSPACE_TARGET_WARNING}"
    )
    + "\n\nExamples:"
    "\n\n1. dagster-graphql"
    f"\n\n2. dagster-graphql -y path/to/{DEFAULT_WORKSPACE_YAML_FILENAME}"
    "\n\n3. dagster-graphql -f path/to/file.py -a define_repo"
    "\n\n4. dagster-graphql -m some_module -a define_repo"
    "\n\n5. dagster-graphql -f path/to/file.py -a define_pipeline"
    "\n\n6. dagster-graphql -m some_module -a define_pipeline",
)
@click.version_option(version=__version__)
@click.option(
    "--text", "-t", type=click.STRING, help="GraphQL document to execute passed as a string"
)
@click.option(
    "--file", "-f", type=click.File(), help="GraphQL document to execute passed as a file"
)
@click.option(
    "--predefined",
    "-p",
    type=click.Choice(list(PREDEFINED_QUERIES.keys())),
    help="GraphQL document to execute, from a predefined set provided by dagster-graphql.",
)
@click.option(
    "--variables",
    "-v",
    type=click.STRING,
    help="A JSON encoded string containing the variables for GraphQL execution.",
)
@click.option(
    "--remote",
    "-r",
    type=click.STRING,
    help="A URL for a remote instance running dagster-webserver to send the GraphQL request to.",
)
@click.option(
    "--output",
    "-o",
    type=click.STRING,
    help=(
        "A file path to store the GraphQL response to. This flag is useful when making pipeline/job"
        " execution queries, since pipeline/job execution causes logs to print to stdout and"
        " stderr."
    ),
)
@click.option(
    "--ephemeral-instance",
    is_flag=True,
    default=False,
    help="Use an ephemeral DagsterInstance instead of resolving via DAGSTER_HOME",
)
@workspace_options
def ui(
    text: Optional[str],
    file: Optional[TextIOWrapper],
    predefined: Optional[str],
    variables: Optional[str],
    remote: Optional[str],
    output: Optional[str],
    ephemeral_instance: bool,
    **other_opts,
):
    workspace_opts = WorkspaceOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    query = None
    if text is not None and file is None and predefined is None:
        query = text.strip("'\" \n\t")
    elif file is not None and text is None and predefined is None:
        query = file.read()
    elif predefined is not None and text is None and file is None:
        query = PREDEFINED_QUERIES[predefined]
    else:
        raise click.UsageError(
            "Must select one and only one of text (-t), file (-f), or predefined (-p) "
            "to select GraphQL document to execute."
        )

    if remote:
        res = execute_query_against_remote(remote, query, variables)
        print(res)  # noqa: T201
    else:
        with (
            get_temporary_instance_for_cli() if ephemeral_instance else get_instance_for_cli()
        ) as instance:
            with WorkspaceProcessContext(
                instance=instance,
                version=__version__,
                read_only=False,
                workspace_load_target=workspace_opts.to_load_target(),
            ) as workspace_process_context:
                execute_query_from_cli(
                    workspace_process_context,
                    query,
                    variables,
                    output,
                )


cli = create_dagster_graphql_cli()


def main():
    # click magic
    cli(obj={})  # pylint:disable=E1120
