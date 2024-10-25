
from typing import Mapping

import click

import dagster._check as check
from dagster._cli.utils import get_instance_for_cli, get_possibly_temporary_instance_for_cli
from dagster._cli.workspace.cli_target import (
    get_repository_python_origin_from_kwargs,
    python_origin_target_argument,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.backfill_policy import BackfillPolicyType
from dagster._core.definitions.definitions_load_context import DefinitionsLoadContext, DefinitionsLoadType
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.repository_definition.repository_definition import RepositoryLoadData
from dagster._core.errors import DagsterInvalidSubsetError, DagsterUnknownPartitionError
from dagster._core.execution.api import execute_job
from dagster._core.instance import DagsterInstance
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.telemetry import telemetry_wrapper
from dagster._serdes.utils import serialize_value
from dagster._utils.env import environ
from dagster._utils.hosted_user_process import recon_job_from_origin, recon_repository_from_origin
from dagster._utils.interrupts import capture_interrupts
from numpy import require


@click.group(name="looker")
def app():
    """Commands for working with the dagster-looker integration"""

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

        pending_data = DefinitionsLoadContext.get().get_pending_reconstruction_metadata()
        load_data = RepositoryLoadData(reconstruction_metadata=pending_data) if pending_data else None
        recon_repo = recon_repository_from_origin(repository_origin)
        repo_def = recon_repo.get_definition()

        load_data = load_data if pending_data else repo_def.repository_load_data
        serialize_value(load_data)

        save_to = kwargs["save_to"]
        with open(save_to, "w") as file:
            file.write(serialize_value(load_data))
