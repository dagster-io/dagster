import click
from dagster import _check as check
from dagster._cli.utils import assert_no_remaining_opts
from dagster._cli.workspace.cli_target import (
    PythonPointerOpts,
    get_repository_python_origin_from_cli_opts,
)
from dagster._core.definitions.definitions_load_context import (
    DefinitionsLoadContext,
    DefinitionsLoadType,
)
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._utils.env import environ
from dagster._utils.hosted_user_process import recon_repository_from_origin
from dagster._utils.warnings import beta_warning
from dagster_shared.cli import python_pointer_options
from dagster_shared.serdes.utils import serialize_value

from dagster_fivetran.constants import (
    FIVETRAN_RECONSTRUCTION_METADATA_KEY_PREFIX,
    FIVETRAN_SNAPSHOT_ENV_VAR_NAME,
)

try:
    from dagster_managed_elements.cli import apply_cmd, check_cmd

    @click.group(name="fivetran")
    def main():
        """Commands for working with the dagster-fivetran integration."""

    main.add_command(check_cmd)
    main.add_command(apply_cmd)


except ImportError:

    @click.group(
        name="fivetran",
        help=(
            "In order to use managed Fivetran config, the dagster-managed-elements package must be"
            " installed."
        ),
    )
    def main():
        """Commands for working with the dagster-fivetran integration."""


@main.command(name="snapshot", help="Snapshot Fivetran workspace data")
@click.option("--output-path", "-o", help="Path to save the snapshot to", required=True)
@python_pointer_options
def fivetran_snapshot_command(output_path: str, **other_opts: object) -> None:
    python_pointer_opts = PythonPointerOpts.extract_from_cli_options(other_opts)
    assert_no_remaining_opts(other_opts)

    beta_warning("The `dagster-fivetran snapshot` command")
    with environ({FIVETRAN_SNAPSHOT_ENV_VAR_NAME: "1"}):
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
                if k.startswith(FIVETRAN_RECONSTRUCTION_METADATA_KEY_PREFIX)
            }
        )
        if not load_data.reconstruction_metadata:
            raise click.UsageError("No Fivetran data found in the repository")
        click.echo(f"Saving {len(load_data.reconstruction_metadata)} cached Fivetran data")

        with open(output_path, "w") as file:
            file.write(serialize_value(load_data))
