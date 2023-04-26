from dagster._core.definitions.decorators.hook_decorator import event_list_hook
from dagster._core.definitions.events import HookExecutionResult
from mlflow.entities.run_status import RunStatus


def _create_mlflow_run_hook(name):
    @event_list_hook(name=name, required_resource_keys={"mlflow"})
    def _hook(context, event_list):
        for event in event_list:
            if event.is_step_success:
                _cleanup_on_success(context)
            elif event.is_step_failure:
                mlf = context.resources.mlflow
                mlf.end_run(status=RunStatus.to_string(RunStatus.FAILED))

        return HookExecutionResult(hook_name=name, is_skipped=False)

    return _hook


def _cleanup_on_success(context):
    """Checks if the current solid in the context is the last solid in the job
    and ends the mlflow run with a successful status when this is the case.
    """
    last_solid_name = context._step_execution_context.job_def.nodes_in_topological_order[  # noqa: SLF001  # fmt: skip
        -1
    ].name

    if context.op.name == last_solid_name:
        context.resources.mlflow.end_run()


end_mlflow_on_run_finished = _create_mlflow_run_hook("end_mlflow_on_run_finished")
