from dagster.cli.load_handle import _cli_load_invariant, handle_for_pipeline_cli_args
from dagster.core.definitions.container import get_active_repository_data_from_image
from dagster.core.snap import PipelineSnapshot
from dagster.seven import is_module_available


def get_pipeline_snapshot_from_cli_args(cli_args):
    _cli_load_invariant(cli_args.get('pipeline_name') is not None)

    if cli_args.get('image'):
        _cli_load_invariant(
            is_module_available('docker'),
            msg='--image is not supported without dagster[docker] or the Python package docker installed.',
        )
        active_repo_data = get_active_repository_data_from_image(cli_args.get('image'))
        return active_repo_data.get_pipeline_snapshot(cli_args.get('pipeline_name')[0])
    else:
        pipeline_definition = handle_for_pipeline_cli_args(cli_args).build_pipeline_definition()
        return PipelineSnapshot.from_pipeline_def(pipeline_definition)
