from dagster import check, ExecutionTargetHandle, RunConfig, SystemStorageData

from dagster.core.execution.api import create_execution_plan, scoped_pipeline_context
from dagster.core.execution.results import PipelineExecutionResult

from .config import DaskConfig
from .engine import DaskEngine


def execute_on_dask(
    handle, env_config=None, run_config=None, dask_config=None
):  # pylint: disable=too-many-locals
    check.inst_param(handle, 'handle', ExecutionTargetHandle)
    check.opt_dict_param(env_config, 'env_config', key_type=str)
    dask_config = check.opt_inst_param(dask_config, 'dask_config', DaskConfig, DaskConfig())
    run_config = check.opt_inst_param(
        run_config, 'run_config', RunConfig, RunConfig(executor_config=dask_config)
    )

    check.inst(
        run_config.executor_config,
        DaskConfig,
        'run_config.executor_config should be instance of DaskConfig to execute on Dask',
    )

    pipeline_def = handle.build_pipeline_definition()

    execution_plan = create_execution_plan(pipeline_def, env_config, run_config=run_config)

    with scoped_pipeline_context(pipeline_def, env_config, run_config) as pipeline_context:
        events = list(DaskEngine.execute(pipeline_context, execution_plan, None))

        return PipelineExecutionResult(
            pipeline_def,
            run_config.run_id,
            events,
            lambda: scoped_pipeline_context(
                pipeline_def,
                env_config,
                run_config,
                system_storage_data=SystemStorageData(
                    intermediates_manager=pipeline_context.intermediates_manager,
                    run_storage=pipeline_context.run_storage,
                    file_manager=pipeline_context.file_manager,
                ),
            ),
        )
