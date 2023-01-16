from dagster import _check as check
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.executor.multi_environment.remote_step_information import (
    get_remote_step_info,
)
from dagster._core.instance import DagsterInstance
from dagster._core.origin import PipelinePythonOrigin, RepositoryPythonOrigin
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._grpc.types import ExecuteStepArgs


# So that we can use PipelinePythonOrigin to wrap an ephemeral, in-process job
class InMemoryCodePointer(CodePointer):
    def __init__(self, target):
        self.target = target

    def load_target(self) -> object:
        return self.target

    def describe(self) -> str:
        return "inmem"


def pipeline_origin_for_op(job_def: JobDefinition):
    return pipeline_origin_for_job_in_defs(Definitions(jobs=[job_def]), job_def.name)


def pipeline_origin_for_job_in_defs(
    definitions: Definitions, job_name: str
) -> PipelinePythonOrigin:
    repo = definitions.get_inner_repository_for_loading_process()
    return PipelinePythonOrigin(
        pipeline_name=job_name,
        repository_origin=RepositoryPythonOrigin(
            executable_path="invalid", code_pointer=InMemoryCodePointer(repo)
        ),
    )


def execute_op_within_inprogress_run(
    instance: DagsterInstance,
    job_def: JobDefinition,
    run_id: str,
    step_key: str,
):
    fake_pipeline_origin = pipeline_origin_for_op(job_def)
    dagster_run = check.not_none(instance.get_run_by_id(run_id))
    dagster_run = dagster_run._replace(pipeline_code_origin=fake_pipeline_origin)
    execute_step_in_out_of_proc_step(instance, dagster_run, step_key)


def execute_step_in_out_of_proc_step(
    instance: DagsterInstance,
    dagster_run: DagsterRun,
    step_key: str,
):
    run_id = dagster_run.run_id
    remote_step_info = get_remote_step_info(instance=instance, run_id=run_id, step_key=step_key)

    step_args = ExecuteStepArgs(
        pipeline_origin=check.not_none(dagster_run.pipeline_code_origin),
        pipeline_run_id=run_id,
        step_keys_to_execute=[step_key],
        instance_ref=None,
        retry_mode=remote_step_info.retry_mode,
        known_state=remote_step_info.known_state,
        should_verify_step=False,
    )

    from dagster._cli.api import _execute_step_command_body

    for event in _execute_step_command_body(step_args, instance, dagster_run):
        print(f"processing event in worker {event}")


def defs_for_single_assets_def(assets_def: AssetsDefinition, job_name: str):
    source_assets = []
    for _input_name, asset_keys_for_input in assets_def.keys_by_input_name.items():
        for asset_key in asset_keys_for_input:
            source_assets.append(SourceAsset(asset_key))

    return Definitions(
        jobs=[define_asset_job(job_name)],
        assets=[assets_def, *source_assets],
    )


def execute_asset_within_inprogress_run(
    instance: DagsterInstance,
    assets_def: AssetsDefinition,
    run_id: str,
    step_key: str,
):
    dagster_run = check.not_none(instance.get_run_by_id(run_id), "Run must exist in instance")
    job_name = dagster_run.pipeline_name

    in_worker_process_origin = pipeline_origin_for_job_in_defs(
        defs_for_single_assets_def(assets_def, job_name),
        job_name,
    )

    dagster_run = dagster_run._replace(
        pipeline_code_origin=in_worker_process_origin,
        # right now if you do materialize all in dagit it actually fully
        # expands the asset selection to be all the assets. when this
        # gets passed through it fails a subsetting check because the
        # source asset is not executable. So here we only execute the single
        # asset key
        asset_selection=frozenset([assets_def.key]),
    )

    execute_step_in_out_of_proc_step(instance, dagster_run, step_key)
