from dagster.cli.load_handle import _cli_load_invariant, recon_pipeline_for_cli_args
from dagster.core.definitions.container import get_external_repository_from_image
from dagster.core.snap import PipelineSnapshot
from dagster.seven import is_module_available


def get_pipeline_snapshot_from_cli_args(cli_args):
    _cli_load_invariant(cli_args.get('pipeline_name') is not None)

    if cli_args.get('image'):
        _cli_load_invariant(
            is_module_available('docker'),
            msg='--image is not supported without dagster[docker] or the Python package docker installed.',
        )
        external_repo = get_external_repository_from_image(cli_args.get('image'))
        return external_repo.get_external_pipeline(
            cli_args.get('pipeline_name')[0]
        ).pipeline_snapshot
    else:
        pipeline_def = recon_pipeline_for_cli_args(cli_args).get_definition()
        return PipelineSnapshot.from_pipeline_def(pipeline_def)
