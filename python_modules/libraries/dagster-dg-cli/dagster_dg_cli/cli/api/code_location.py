"""Code location API commands following GitHub CLI patterns."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.code_location import DgApiCodeLocationDocument

import click
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.plus.config_utils import dg_api_options

from dagster_dg_cli.cli.api.client import create_dg_api_graphql_client
from dagster_dg_cli.cli.api.formatters import (
    format_add_code_location_result,
    format_code_location,
    format_code_locations,
    format_delete_code_location_result,
)
from dagster_dg_cli.cli.api.shared import handle_api_errors
from dagster_dg_cli.cli.response_schema import dg_response_schema


def build_code_location_document(
    location_name: str,
    location_file: str | None,
    **kwargs: Any,
) -> "DgApiCodeLocationDocument":
    """Build a code location document from CLI args, optionally merging with a YAML file."""
    import yaml

    from dagster_dg_cli.api_layer.schemas.code_location import (
        DgApiCodeLocationDocument,
        DgApiCodeSource,
        DgApiGitMetadata,
    )

    location_doc_from_file: dict[str, Any] = {}

    if location_file:
        with open(location_file, encoding="utf8") as f:
            location_doc_from_file = yaml.safe_load(f.read()) or {}

        if "locations" in location_doc_from_file:
            locations_by_name = {
                loc["location_name"]: loc for loc in location_doc_from_file["locations"]
            }
            if location_name not in locations_by_name:
                raise click.UsageError(
                    f"No location with name '{location_name}' defined in location file."
                )
            location_doc_from_file = locations_by_name[location_name]
        elif (
            location_doc_from_file.get("location_name")
            and location_doc_from_file["location_name"] != location_name
        ):
            raise click.UsageError(
                f"Name provided via argument and in location file does not match: "
                f"'{location_name}' != '{location_doc_from_file['location_name']}'."
            )

    # Merge file values with CLI args (CLI args take precedence)
    file_code_source = location_doc_from_file.get("code_source", {})
    file_git = location_doc_from_file.get("git", {})

    merged_code_source = DgApiCodeSource(
        python_file=kwargs.get("python_file") or file_code_source.get("python_file"),
        module_name=kwargs.get("module_name") or file_code_source.get("module_name"),
        package_name=kwargs.get("package_name") or file_code_source.get("package_name"),
        autoload_defs_module_name=file_code_source.get("autoload_defs_module_name"),
    )
    has_merged_code_source = any(v is not None for v in merged_code_source.model_dump().values())

    merged_git = DgApiGitMetadata(
        commit_hash=kwargs.get("commit_hash") or file_git.get("commit_hash"),
        url=kwargs.get("git_url") or file_git.get("url"),
    )
    has_merged_git = any(v is not None for v in merged_git.model_dump().values())

    return DgApiCodeLocationDocument(
        location_name=location_name,
        image=kwargs.get("image") or location_doc_from_file.get("image"),
        code_source=merged_code_source if has_merged_code_source else None,
        working_directory=kwargs.get("working_directory")
        or location_doc_from_file.get("working_directory"),
        executable_path=kwargs.get("executable_path")
        or location_doc_from_file.get("executable_path"),
        attribute=kwargs.get("attribute") or location_doc_from_file.get("attribute"),
        git=merged_git if has_merged_git else None,
    )


@click.command(name="add", cls=DgClickCommand)
@click.argument("location_name", type=str)
@click.option("--image", type=str, help="Docker image for the code location")
@click.option("-m", "--module-name", type=str, help="Python module name")
@click.option("-p", "--package-name", type=str, help="Python package name")
@click.option("-f", "--python-file", type=str, help="Python file path")
@click.option("-d", "--working-directory", type=str, help="Working directory")
@click.option("--executable-path", type=str, help="Python executable path")
@click.option("-a", "--attribute", type=str, help="Attribute to load definitions from")
@click.option("--commit-hash", type=str, help="Git commit hash")
@click.option("--git-url", type=str, help="Git repository URL")
@click.option(
    "--location-file",
    "--from",
    "location_file",
    type=click.Path(exists=True),
    help="YAML file with location configuration",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.code_location", cls="DgApiAddCodeLocationResult"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def add_code_location_command(
    ctx: click.Context,
    location_name: str,
    image: str | None,
    module_name: str | None,
    package_name: str | None,
    python_file: str | None,
    working_directory: str | None,
    executable_path: str | None,
    attribute: str | None,
    commit_hash: str | None,
    git_url: str | None,
    location_file: str | None,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Add or update a code location in the deployment."""
    from dagster_dg_cli.api_layer.api.code_location import DgApiCodeLocationApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiCodeLocationApi(client)

    with handle_api_errors(ctx, output_json):
        document = build_code_location_document(
            location_name=location_name,
            location_file=location_file,
            image=image,
            module_name=module_name,
            package_name=package_name,
            python_file=python_file,
            working_directory=working_directory,
            executable_path=executable_path,
            attribute=attribute,
            commit_hash=commit_hash,
            git_url=git_url,
        )
        result = api.add_code_location(document)
        output = format_add_code_location_result(result, as_json=output_json)
        click.echo(output)


@click.command(name="list", cls=DgClickCommand)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.code_location", cls="DgApiCodeLocationList"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def list_code_locations_command(
    ctx: click.Context,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """List code locations in the deployment."""
    from dagster_dg_cli.api_layer.api.code_location import DgApiCodeLocationApi

    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    api = DgApiCodeLocationApi(client)

    with handle_api_errors(ctx, output_json):
        locations = api.list_code_locations()
        output = format_code_locations(locations, as_json=output_json)
        click.echo(output)


@click.command(name="get", cls=DgClickCommand)
@click.argument("location_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.code_location", cls="DgApiCodeLocation"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def get_code_location_command(
    ctx: click.Context,
    location_name: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Get detailed information about a specific code location."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.code_location import DgApiCodeLocationApi

    api = DgApiCodeLocationApi(client)

    with handle_api_errors(ctx, output_json):
        location = api.get_code_location(location_name)
        if location is None:
            raise click.ClickException(f"Code location '{location_name}' not found.")
        output = format_code_location(location, as_json=output_json)
        click.echo(output)


@click.command(name="delete", cls=DgClickCommand)
@click.argument("location_name", type=str)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine readability",
)
@dg_response_schema(
    module="dagster_dg_cli.api_layer.schemas.code_location", cls="DgApiDeleteCodeLocationResult"
)
@dg_api_options(deployment_scoped=True)
@cli_telemetry_wrapper
@click.pass_context
def delete_code_location_command(
    ctx: click.Context,
    location_name: str,
    output_json: bool,
    organization: str,
    deployment: str,
    api_token: str,
    view_graphql: bool,
) -> None:
    """Delete a code location from the deployment."""
    config = DagsterPlusCliConfig.create_for_deployment(
        deployment=deployment,
        organization=organization,
        user_token=api_token,
    )
    client = create_dg_api_graphql_client(ctx, config, view_graphql=view_graphql)
    from dagster_dg_cli.api_layer.api.code_location import DgApiCodeLocationApi

    api = DgApiCodeLocationApi(client)

    with handle_api_errors(ctx, output_json):
        result = api.delete_code_location(location_name)
        output = format_delete_code_location_result(result, as_json=output_json)
        click.echo(output)


@click.group(
    name="code-location",
    cls=DgClickGroup,
    commands={
        "add": add_code_location_command,
        "delete": delete_code_location_command,
        "get": get_code_location_command,
        "list": list_code_locations_command,
    },
)
def code_location_group():
    """Manage code locations in Dagster Plus."""
