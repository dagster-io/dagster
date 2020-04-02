from dagster.cli.load_handle import (
    _cli_load_invariant,
    handle_for_pipeline_cli_args,
    handle_for_repo_cli_args,
)
from dagster.core.definitions.container import get_container_snapshot
from dagster.core.snap.pipeline_snapshot import PipelineSnapshot
from dagster.core.snap.repository_snapshot import RepositorySnapshot
from dagster.seven import is_module_available


def get_pipeline_snapshot_from_cli_args(cli_args):
    _cli_load_invariant(cli_args.get('pipeline_name') is not None)

    if cli_args.get('image'):
        _cli_load_invariant(
            is_module_available('docker'),
            msg='--image is not supported without dagster[docker] or the Python package docker installed.',
        )
        repository_snapshot = get_container_snapshot(cli_args.get('image'))
        return repository_snapshot.get_pipeline_snapshot(cli_args.get('pipeline_name')[0])
    else:
        pipeline_definition = handle_for_pipeline_cli_args(cli_args).build_pipeline_definition()
        return PipelineSnapshot.from_pipeline_def(pipeline_definition)


def get_repository_snapshot_from_cli_args(cli_args):
    if cli_args.get('image'):
        _cli_load_invariant(
            is_module_available('docker'),
            msg='--image is not supported without dagster[docker] or the Python package docker installed.',
        )
        return get_container_snapshot(cli_args.get('image'))
    return RepositorySnapshot.from_repository_definition(
        handle_for_repo_cli_args(cli_args).build_repository_definition()
    )
