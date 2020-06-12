import dask
import dask.distributed
from dagster_graphql.client.mutations import execute_execute_plan_mutation

from dagster import check, seven
from dagster.core.engine.engine_base import Engine
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.utils import frozentags
from dagster.utils.hosted_user_process import create_in_process_ephemeral_workspace

from .config import DaskConfig

# Dask resource requirements are specified under this key
DASK_RESOURCE_REQUIREMENTS_KEY = 'dagster-dask/resource_requirements'


def query_on_dask_worker(
    workspace, variables, dependencies, instance_ref=None
):  # pylint: disable=unused-argument
    '''Note that we need to pass "dependencies" to ensure Dask sequences futures during task
    scheduling, even though we do not use this argument within the function.
    '''
    return execute_execute_plan_mutation(workspace, variables, instance_ref=instance_ref)


def get_dask_resource_requirements(tags):
    check.inst_param(tags, 'tags', frozentags)
    req_str = tags.get(DASK_RESOURCE_REQUIREMENTS_KEY)
    if req_str is not None:
        return seven.json.loads(req_str)

    return {}


class DaskEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        dask_config = pipeline_context.executor_config

        check.param_invariant(
            isinstance(pipeline_context.executor_config, DaskConfig),
            'pipeline_context',
            'Expected executor_config to be DaskConfig got {}'.format(
                pipeline_context.executor_config
            ),
        )

        # Checks to ensure storage is compatible with Dask configuration
        storage = pipeline_context.run_config.get('storage')
        check.invariant(storage.keys(), 'Must specify storage to use Dask execution')

        check.invariant(
            pipeline_context.instance.is_persistent,
            'Dask execution requires a persistent DagsterInstance',
        )

        # https://github.com/dagster-io/dagster/issues/2440
        check.invariant(
            pipeline_context.system_storage_def.is_persistent,
            'Cannot use in-memory storage with Dask, use filesystem, S3, or GCS',
        )

        step_levels = execution_plan.execution_step_levels()

        pipeline_name = pipeline_context.pipeline_def.name

        instance = pipeline_context.instance

        cluster_type = dask_config.cluster_type
        if cluster_type == 'local':
            from dask.distributed import LocalCluster

            cluster = LocalCluster(**dask_config.build_dict(pipeline_name))
        elif cluster_type == 'yarn':
            from dask_yarn import YarnCluster

            cluster = YarnCluster(**dask_config.build_dict(pipeline_name))
        elif cluster_type == 'ssh':
            from dask.distributed import SSHCluster

            cluster = SSHCluster(**dask_config.build_dict(pipeline_name))
        elif cluster_type == 'pbs':
            from dask_jobqueue import PBSCluster

            cluster = PBSCluster(**dask_config.build_dict(pipeline_name))
        elif cluster_type == 'kube':
            from dask_kubernetes import KubeCluster

            cluster = KubeCluster(**dask_config.build_dict(pipeline_name))
        else:
            raise ValueError(
                f"Must be providing one of the following ('local', 'yarn', 'ssh', 'pbs', 'kube') not {cluster_type}"
            )

        with dask.distributed.Client(cluster) as client:
            execution_futures = []
            execution_futures_dict = {}

            for step_level in step_levels:
                for step in step_level:
                    # We ensure correctness in sequencing by letting Dask schedule futures and
                    # awaiting dependencies within each step.
                    dependencies = []
                    for step_input in step.step_inputs:
                        for key in step_input.dependency_keys:
                            dependencies.append(execution_futures_dict[key])

                    run_config = dict(pipeline_context.run_config, execution={'in_process': {}})
                    recon_repo = pipeline_context.pipeline.get_reconstructable_repository()
                    variables = {
                        'executionParams': {
                            'selector': {
                                'pipelineName': pipeline_name,
                                'repositoryName': recon_repo.get_definition().name,
                                'repositoryLocationName': '<<in_process>>',
                            },
                            'runConfigData': run_config,
                            'mode': pipeline_context.mode_def.name,
                            'executionMetadata': {'runId': pipeline_context.pipeline_run.run_id},
                            'stepKeys': [step.key],
                        }
                    }

                    dask_task_name = '%s.%s' % (pipeline_name, step.key)

                    workspace = create_in_process_ephemeral_workspace(
                        pointer=pipeline_context.pipeline.get_reconstructable_repository().pointer
                    )

                    future = client.submit(
                        query_on_dask_worker,
                        workspace,
                        variables,
                        dependencies,
                        instance.get_ref(),
                        key=dask_task_name,
                        resources=get_dask_resource_requirements(step.tags),
                    )

                    execution_futures.append(future)
                    execution_futures_dict[step.key] = future

            # This tells Dask to awaits the step executions and retrieve their results to the
            # master
            for future in dask.distributed.as_completed(execution_futures):
                for step_event in future.result():
                    check.inst(step_event, DagsterEvent)

                    yield step_event
