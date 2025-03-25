import click
from dagster import _check as check
from dagster._cli.utils import assert_no_remaining_opts
from dagster._cli.workspace.cli_target import (
    PythonPointerOpts,
    get_repository_python_origin_from_cli_opts,
    python_pointer_options,
)
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._utils.env import environ
from dagster._utils.hosted_user_process import recon_repository_from_origin
from dagster._utils.warnings import beta_warning
from dagster_shared.serdes.utils import serialize_value

SNAPSHOT_ENV_VAR_NAME = "DAGSTER_SIGMA_IS_GENERATING_SNAPSHOT"
SIGMA_RECON_DATA_PREFIX = "sigma_"


@click.group(name="sigma")
def app():
    """Commands for working with the dagster-sigma integration."""


@app.command(name="snapshot", help="Snapshot sigma instance data")
@click.option("--output-path", "-o", help="Path to save the snapshot to", required=True)
@python_pointer_options
def sigma_snapshot_command(output_path: str, **other_opts: object) -> None:
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    beta_warning("The `dagster-sigma snapshot` command")
    with environ({SNAPSHOT_ENV_VAR_NAME: "1"}):
        DefinitionsLoadContext.set(
            DefinitionsLoadContext(
                load_type=DefinitionsLoadType.INITIALIZATION, repository_load_data=None
            )
        )
        repository_origin = get_repository_python_origin_from_cli_opts(python_pointer_opts)

        pending_data = DefinitionsLoadContext.get().get_pending_reconstruction_metadata()
        load_data = (
            RepositoryLoadData(reconstruction_metadata=pending_data) if pending_data else None
        )
        recon_repo = recon_repository_from_origin(repository_origin)
        repo_def = recon_repo.get_definition()

        load_data = load_data if pending_data else repo_def.repository_load_data
        load_data = RepositoryLoadData(
            reconstruction_metadata={
                k: v
                for k, v in check.not_none(load_data).reconstruction_metadata.items()
                if k.startswith(SIGMA_RECON_DATA_PREFIX)
            }
        )
        if not load_data.reconstruction_metadata:
            raise click.UsageError("No Sigma data found in the repository")
        click.echo(f"Saving {len(load_data.reconstruction_metadata)} cached Sigma data")

        with open(output_path, "w") as file:
            file.write(serialize_value(load_data))
