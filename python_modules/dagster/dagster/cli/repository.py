import os
import sys

import click

from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.cli.pipeline import repository_target_argument
from dagster.core.snap.repository_snapshot import RepositorySnapshot
from dagster.serdes import serialize_dagster_namedtuple


def create_repository_cli_group():
    group = click.Group(name='repository')
    group.add_command(snapshot_command)
    return group


@click.command(
    name='snapshot',
    help='Snapshot the given repository definition and load into the serialization target.',
)
@click.argument('output_file', type=click.Path())
@repository_target_argument
def snapshot_command(output_file, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)

    # add the path for the cwd so imports in dynamically loaded code work correctly
    sys.path.append(os.getcwd())

    definition = handle.entrypoint.perform_load()
    repository_snapshot = RepositorySnapshot.from_repository_definition(definition)
    with open(os.path.abspath(output_file), 'w+') as fp:
        fp.write(serialize_dagster_namedtuple(repository_snapshot))


repository_cli = create_repository_cli_group()
