from urllib.parse import urljoin, urlparse

import click
import requests
from dagster import check, seven
from dagster.cli.workspace import workspace_target_argument
from dagster.cli.workspace.cli_target import WORKSPACE_TARGET_WARNING, get_workspace_from_kwargs
from dagster.cli.workspace.context import WorkspaceProcessContext
from dagster.cli.workspace.workspace import Workspace
from dagster.core.instance import DagsterInstance
from dagster.utils import DEFAULT_WORKSPACE_YAML_FILENAME
from dagster.utils.log import get_stack_trace_array
from graphql import graphql
from graphql.execution.executors.gevent import GeventExecutor
from graphql.execution.executors.sync import SyncExecutor

from .client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from .schema import create_schema
from .version import __version__

from future.standard_library import install_aliases  # isort:skip

install_aliases()  # isort:skip


def create_dagster_graphql_cli():
    return ui


def execute_query(workspace, query, variables=None, use_sync_executor=False, instance=None):
    check.inst_param(workspace, "workspace", Workspace)
    check.str_param(query, "query")
    check.opt_dict_param(variables, "variables")
    instance = (
        check.inst_param(instance, "instance", DagsterInstance)
        if instance
        else DagsterInstance.get()
    )
    check.bool_param(use_sync_executor, "use_sync_executor")

    query = query.strip("'\" \n\t")

    context = WorkspaceProcessContext(
        workspace=workspace, instance=instance, version=__version__
    ).create_request_context()

    executor = SyncExecutor() if use_sync_executor else GeventExecutor()

    result = graphql(
        request_string=query,
        schema=create_schema(),
        context_value=context,
        variable_values=variables,
        executor=executor,
    )

    result_dict = result.to_dict()

    # Here we detect if this is in fact an error response
    # If so, we iterate over the result_dict and the original result
    # which contains a GraphQLError. If that GraphQL error contains
    # an original_error property (which is the exception the resolver
    # has thrown, typically) we serialize the stack trace of that exception
    # in the 'stack_trace' property of each error to ease debugging

    if "errors" in result_dict:
        check.invariant(len(result_dict["errors"]) == len(result.errors))
        for python_error, error_dict in zip(result.errors, result_dict["errors"]):
            if hasattr(python_error, "original_error") and python_error.original_error:
                error_dict["stack_trace"] = get_stack_trace_array(python_error.original_error)

    return result_dict


def execute_query_from_cli(workspace, query, instance, variables=None, output=None):
    check.inst_param(workspace, "workspace", Workspace)
    check.str_param(query, "query")
    check.inst_param(instance, "instance", DagsterInstance)
    check.opt_str_param(variables, "variables")
    check.opt_str_param(output, "output")

    query = query.strip("'\" \n\t")

    result_dict = execute_query(
        workspace,
        query,
        instance=instance,
        variables=seven.json.loads(variables) if variables else None,
    )
    str_res = seven.json.dumps(result_dict)

    # Since this the entry point for CLI execution, some tests depend on us putting the result on
    # stdout
    if output:
        check.str_param(output, "output")
        with open(output, "w") as f:
            f.write(str_res + "\n")
    else:
        print(str_res)  # pylint: disable=print-call

    return str_res


def execute_query_against_remote(host, query, variables):
    parsed_url = urlparse(host)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise click.UsageError(
            "Host {host} is not a valid URL. Host URL should include scheme ie http://localhost".format(
                host=host
            )
        )

    sanity_check = requests.get(urljoin(host, "/dagit_info"))
    sanity_check.raise_for_status()
    if "dagit" not in sanity_check.text:
        raise click.UsageError(
            "Host {host} failed sanity check. It is not a dagit server.".format(host=host)
        )

    response = requests.post(
        urljoin(host, "/graphql"), params={"query": query, "variables": variables}
    )
    response.raise_for_status()
    str_res = response.json()
    return str_res


PREDEFINED_QUERIES = {
    "launchPipelineExecution": LAUNCH_PIPELINE_EXECUTION_MUTATION,
}


@workspace_target_argument
@click.command(
    name="ui",
    help=(
        "Run a GraphQL query against the dagster interface to a specified repository or pipeline."
        "\n\n{warning}".format(warning=WORKSPACE_TARGET_WARNING)
    )
    + (
        "\n\nExamples:"
        "\n\n1. dagster-graphql"
        "\n\n2. dagster-graphql -y path/to/{default_filename}"
        "\n\n3. dagster-graphql -f path/to/file.py -a define_repo"
        "\n\n4. dagster-graphql -m some_module -a define_repo"
        "\n\n5. dagster-graphql -f path/to/file.py -a define_pipeline"
        "\n\n6. dagster-graphql -m some_module -a define_pipeline"
    ).format(default_filename=DEFAULT_WORKSPACE_YAML_FILENAME),
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
    type=click.Choice(PREDEFINED_QUERIES.keys()),
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
    help="A URL for a remote instance running dagit server to send the GraphQL request to.",
)
@click.option(
    "--output",
    "-o",
    type=click.STRING,
    help="A file path to store the GraphQL response to. This flag is useful when making pipeline "
    "execution queries, since pipeline execution causes logs to print to stdout and stderr.",
)
def ui(text, file, predefined, variables, remote, output, **kwargs):
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
        print(res)  # pylint: disable=print-call
    else:
        instance = DagsterInstance.get()
        with get_workspace_from_kwargs(kwargs) as workspace:
            execute_query_from_cli(
                workspace,
                query,
                instance,
                variables,
                output,
            )


cli = create_dagster_graphql_cli()


def main():
    # click magic
    cli(obj={})  # pylint:disable=E1120
