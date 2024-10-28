import click
from dagster._cli.workspace.cli_target import (
    get_repository_python_origin_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._serdes.utils import serialize_value
from dagster._utils.env import environ
from dagster._utils.hosted_user_process import recon_repository_from_origin


@click.group(name="looker")
def app():
    """Commands for working with the dagster-looker integration."""


@app.command(name="snapshot", help="Snapshot looker instance data")
@python_origin_target_argument
@click.option("--save-to", "-s", help="Path to save the snapshot to", required=True)
def looker_snapshot_command(**kwargs) -> None:
    with environ({"DAGSTER_LOOKER_IS_GENERATING_SNAPSHOT": "1"}):
        DefinitionsLoadContext.set(
            DefinitionsLoadContext(
                load_type=DefinitionsLoadType.INITIALIZATION, repository_load_data=None
            )
        )
        repository_origin = get_repository_python_origin_from_kwargs(kwargs)

        recon_repo = recon_repository_from_origin(repository_origin)
        repo_def = recon_repo.get_definition()

        load_data = repo_def.repository_load_data
        serialize_value(load_data)

        save_to = kwargs["save_to"]
        with open(save_to, "w") as file:
            file.write(serialize_value(load_data))
