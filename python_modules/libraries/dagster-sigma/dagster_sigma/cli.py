import click
from dagster._cli.workspace.cli_target import (
    get_repository_python_origin_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._serdes.utils import serialize_value
from dagster._utils.env import environ
from dagster._utils.hosted_user_process import recon_repository_from_origin

SNAPSHOT_ENV_VAR_NAME = "DAGSTER_SIGMA_IS_GENERATING_SNAPSHOT"


@click.group(name="sigma")
def app():
    """Commands for working with the dagster-sigma integration."""


@app.command(name="snapshot", help="Snapshot sigma instance data")
@python_origin_target_argument
@click.option("--save-to", "-s", help="Path to save the snapshot to", required=True)
def sigma_snapshot_command(**kwargs) -> None:
    with environ({SNAPSHOT_ENV_VAR_NAME: "1"}):
        DefinitionsLoadContext.set(
            DefinitionsLoadContext(
                load_type=DefinitionsLoadType.INITIALIZATION, repository_load_data=None
            )
        )

        repository_origin = get_repository_python_origin_from_kwargs(kwargs)

        pending_data = DefinitionsLoadContext.get().get_pending_reconstruction_metadata()
        load_data = (
            RepositoryLoadData(reconstruction_metadata=pending_data) if pending_data else None
        )
        recon_repo = recon_repository_from_origin(repository_origin)
        repo_def = recon_repo.get_definition()

        load_data = load_data if pending_data else repo_def.repository_load_data
        load_data = RepositoryLoadData(
            reconstruction_metadata={
                k: v for k, v in load_data.reconstruction_metadata.items() if k.startswith("sigma_")
            }
        )
        if not load_data.reconstruction_metadata:
            raise click.UsageError("No Sigma data found in the repository")
        click.echo(f"Saving {len(load_data.reconstruction_metadata)} cached Sigma data")

        save_to = kwargs["save_to"]
        with open(save_to, "w") as file:
            file.write(serialize_value(load_data))
