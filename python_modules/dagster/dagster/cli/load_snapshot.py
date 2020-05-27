from dagster.cli.load_handle import _cli_load_invariant, recon_pipeline_for_cli_args
from dagster.core.snap import PipelineSnapshot


def get_pipeline_snapshot_from_cli_args(cli_args):
    _cli_load_invariant(cli_args.get('pipeline_name') is not None)
    pipeline_def = recon_pipeline_for_cli_args(cli_args).get_definition()
    return PipelineSnapshot.from_pipeline_def(pipeline_def)
