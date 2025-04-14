import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import yaml
from dagster_shared import check
from dagster_shared.serdes.serdes import deserialize_value
from typer import Argument, Option, Typer

from dagster_cloud_cli import gql, ui
from dagster_cloud_cli.config_utils import (
    DEFAULT_LOCATION_LOAD_TIMEOUT,
    DEPLOYMENT_CLI_OPTIONS,
    dagster_cloud_options,
    get_location_document,
)
from dagster_cloud_cli.core.graphql_client import DagsterCloudGraphQLClient
from dagster_cloud_cli.core.workspace import CodeLocationDeployData
from dagster_cloud_cli.utils import add_options

DEFAULT_LOCATIONS_YAML_FILENAME = "locations.yaml"

app = Typer(help="Manage your Dagster Cloud workspace.")


def _get_location_input(location: str, kwargs: dict[str, Any]) -> gql.CliInputCodeLocation:
    python_file = kwargs.get("python_file")

    return gql.CliInputCodeLocation(
        name=location,
        python_file=str(python_file) if python_file else None,
        package_name=kwargs.get("package_name"),
        image=kwargs.get("image"),
        module_name=kwargs.get("module_name"),
        working_directory=kwargs.get("working_directory"),
        executable_path=kwargs.get("executable_path"),
        attribute=kwargs.get("attribute"),
        commit_hash=(
            kwargs["git"].get("commit_hash") if "git" in kwargs else kwargs.get("commit_hash")
        ),
        url=kwargs["git"].get("url") if "git" in kwargs else kwargs.get("git_url"),
    )


def _add_or_update_location(
    client: DagsterCloudGraphQLClient,
    location_document: dict[str, Any],
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    url: Optional[str] = None,
) -> None:
    try:
        gql.add_or_update_code_location(client, location_document)
        name = location_document["location_name"]
        ui.print(f"Added or updated location {name}.")
        wait_for_load(
            client,
            [name],
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )
    except Exception as e:
        raise ui.error(str(e))


@app.command(name="add-location", short_help="Add or update a code location image.")
@dagster_cloud_options(allow_empty=True, requires_url=True)
@add_options(DEPLOYMENT_CLI_OPTIONS)
def add_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    location: str = Argument(None, help="Code location name."),
    **kwargs,
):
    """Add or update the image for a code location in the deployment."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        location_document = get_location_document(location, kwargs)
        _add_or_update_location(
            client,
            location_document,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )


def list_locations(location_names: list[str]) -> str:
    if len(location_names) == 0:
        return ""
    elif len(location_names) == 1:
        return location_names[0]
    else:
        return f"{', '.join(location_names[:-1])}, and {location_names[-1]}"


@app.command(name="update-location", short_help="Update a code location image.")
@dagster_cloud_options(allow_empty=True, requires_url=True)
@add_options(DEPLOYMENT_CLI_OPTIONS)
def update_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    location: str = Argument(None, help="Code location name."),
    **kwargs,
):
    """Update the image for a code location in a deployment."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        location_document = get_location_document(location, kwargs)
        _add_or_update_location(
            client,
            location_document,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )


def _format_error(load_error: Mapping[str, Any]):
    result = [
        load_error["message"],
        "".join(load_error["stack"]),
    ]

    for chain_link in load_error["errorChain"]:
        result.append(
            "The above exception was caused by the following exception:"
            if chain_link["isExplicitLink"]
            else "The above exception occurred during handling of the following exception:"
        )

        result.extend([chain_link["error"]["message"], "".join(chain_link["error"]["stack"])])

    return "\n".join(result)


def wait_for_load(
    client,
    locations,
    location_load_timeout=DEFAULT_LOCATION_LOAD_TIMEOUT,
    agent_heartbeat_timeout=DEFAULT_LOCATION_LOAD_TIMEOUT,
    url: Optional[str] = None,
):
    start_time = time.time()
    if url:
        ui.print(f"View the status of your locations at {url}/locations.\n")
    ui.print(f"Waiting for agent to sync changes to {list_locations(locations)}...")

    if not location_load_timeout and not agent_heartbeat_timeout:
        return

    has_agent_heartbeat = False
    iterations = 0
    while True:
        if not has_agent_heartbeat:
            if time.time() - start_time > agent_heartbeat_timeout:
                raise ui.error(
                    "No Dagster Cloud agent is actively heartbeating. Make sure that you have a"
                    " Dagster Cloud agent running."
                )
            try:
                agents = gql.fetch_agent_status(client)
            except Exception as e:
                raise ui.error("Unable to query agent status: " + str(e))

            has_agent_heartbeat = any(a["status"] == "RUNNING" for a in agents)

        if time.time() - start_time > location_load_timeout:
            raise ui.error("Timed out waiting for location data to update.")

        try:
            nodes = gql.fetch_code_locations(client)
        except Exception as e:
            raise ui.error(str(e))

        nodes_by_location = {node["name"]: node for node in nodes}

        if all(
            location in nodes_by_location
            and nodes_by_location[location].get("loadStatus") == "LOADED"
            for location in locations
        ):
            error_locations = [
                location
                for location in locations
                if "locationOrLoadError" in nodes_by_location[location]
                and nodes_by_location[location]["locationOrLoadError"]["__typename"]
                == "PythonError"
            ]

            if error_locations:
                error_string = (
                    "Some locations failed to load after being synced by the agent:\n"
                    + "\n".join(
                        [
                            f"Error loading {error_location}:\n"
                            f"{_format_error(nodes_by_location[error_location]['locationOrLoadError'])}"
                            for error_location in error_locations
                        ]
                    )
                )
                raise ui.error(error_string)
            else:
                ui.print(
                    f"Agent synced changes to {list_locations(locations)}. Changes should now be"
                    " visible in Dagster Cloud."
                )
                break

        time.sleep(3)
        iterations += 1

        if iterations % 3 == 0:
            ui.print(
                f"Still waiting for agent to sync changes to {list_locations(locations)}. This can"
                " take a few minutes."
            )


@app.command(
    name="delete-location",
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
def delete_command(
    api_token: str,
    url: str,
    deployment: Optional[str],
    location: str = Argument(..., help="Code location name."),
):
    """Delete a code location from the deployment."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        try:
            gql.delete_code_location(client, location)
            ui.print(f"Deleted location {location}.")
        except Exception as e:
            raise ui.error(str(e))


@app.command(
    name="list",
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
def list_command(
    url: str,
    deployment: Optional[str],
    api_token: str,
):
    """List code locations in the deployment."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        execute_list_command(client)


def execute_list_command(client):
    list_res = gql.fetch_workspace_entries(client)

    ui.print("Listing locations...")

    for location in list_res:
        metadata = deserialize_value(
            location["serializedDeploymentMetadata"], CodeLocationDeployData
        )

        location_desc = [location["locationName"]]
        if metadata.python_file:
            location_desc.append(f"File: {metadata.python_file}")
        if metadata.package_name:
            location_desc.append(f"Package: {metadata.package_name}")
        if metadata.image:
            location_desc.append(f"Image: {metadata.image}")

        ui.print("\t".join(location_desc))


@app.command(name="pull")
@dagster_cloud_options(allow_empty=True, requires_url=True)
def pull_command(
    url: str,
    api_token: str,
    deployment: Optional[str],
):
    """Retrieve code location definitions as a workspace.yaml file."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        document = gql.fetch_locations_as_document(client)
        ui.print_yaml(document or {})


@app.command(
    name="sync",
    short_help="Sync deployment code locations with a workspace.yaml file.",
)
@dagster_cloud_options(allow_empty=True, requires_url=True)
def sync_command(
    url: str,
    api_token: str,
    deployment: Optional[str],
    location_load_timeout: int,
    agent_heartbeat_timeout: int,
    workspace: Path = Option(
        "workspace.yaml",
        "--workspace",
        "-w",
        exists=True,
        help="Path to workspace file.",
    ),
):
    """Sync the workspace with the contents of a workspace.yaml file."""
    with gql.graphql_client_from_url(url, api_token, deployment_name=deployment) as client:
        execute_sync_command(
            client,
            workspace,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )


def format_workspace_config(workspace_config) -> dict[str, Any]:
    """Ensures the input workspace config is in the modern format, migrating an input
    in the old format if need be.
    """
    check.dict_param(workspace_config, "workspace_config")

    if isinstance(workspace_config.get("locations"), dict):
        # Convert legacy formatted locations to modern format
        updated_locations = []
        for name, location in workspace_config["locations"].items():
            new_location = {
                k: v
                for k, v in location.items()
                if k not in ("python_file", "package_name", "module_name")
            }
            new_location["code_source"] = {}
            if "python_file" in location:
                new_location["code_source"]["python_file"] = location["python_file"]
            if "package_name" in location:
                new_location["code_source"]["package_name"] = location["package_name"]
            if "module_name" in location:
                new_location["code_source"]["module_name"] = location["module_name"]

            new_location["location_name"] = name
            updated_locations.append(new_location)
        return {"locations": updated_locations}
    else:
        check.is_list(workspace_config.get("locations"))
        return workspace_config


def execute_sync_command(
    client, workspace, location_load_timeout, agent_heartbeat_timeout, url: Optional[str] = None
):
    with open(str(workspace), encoding="utf8") as f:
        config = yaml.load(f.read(), Loader=yaml.SafeLoader)
        processed_config = format_workspace_config(config)

    try:
        locations = gql.reconcile_code_locations(client, processed_config)
        ui.print(f"Synced locations: {', '.join(locations)}")
        wait_for_load(
            client,
            locations,
            location_load_timeout=location_load_timeout,
            agent_heartbeat_timeout=agent_heartbeat_timeout,
            url=url,
        )
    except Exception as e:
        raise ui.error(str(e))
