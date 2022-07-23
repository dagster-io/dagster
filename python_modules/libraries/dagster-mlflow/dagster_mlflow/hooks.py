from mlflow.entities.run_status import RunStatus

from dagster.core.definitions.decorators.hook_decorator import event_list_hook
from dagster.core.definitions.events import HookExecutionResult


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
    """
    Checks if the current solid in the context is the last solid in the pipeline
    and ends the mlflow run with a successful status when this is the case.
    """
    last_solid_name = context._step_execution_context.pipeline_def.solids_in_topological_order[  # pylint: disable=protected-access
        -1
    ].name

    if context.solid.name == last_solid_name:
        context.resources.mlflow.end_run()


end_mlflow_run_on_pipeline_finished = _create_mlflow_run_hook("end_mlflow_run_on_pipeline_finished")
end_mlflow_on_run_finished = _create_mlflow_run_hook("end_mlflow_on_run_finished")
