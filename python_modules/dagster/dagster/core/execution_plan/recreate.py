from dagster import check

from dagster.core.execution import yield_context

from .create import create_execution_plan_from_steps
from .objects import (
    ExecutionPlanInfo,
    ExecutionPlanMeta,
    ExecutionStep,
    StepInput,
    StepOutput,
    StepTag,
)

from .transform import create_transform_compute_fn


def recreate_step_input(plan_info, step_input_meta):
    return StepInput(
        meta=step_input_meta,
        dagster_type=plan_info.pipeline.type_named(step_input_meta.dagster_type_name),
    )


def recreate_step_output(plan_info, step_output_meta):
    return StepOutput(
        meta=step_output_meta,
        dagster_type=plan_info.pipeline.type_named(step_output_meta.dagster_type_name),
    )


def recreate_compute_fn(plan_info, step_meta):
    if step_meta.tag == StepTag.TRANSFORM:
        return create_transform_compute_fn(plan_info, step_meta)
    else:
        check.failed('Unsupported tag {tag}'.format(tag=step_meta.tag))


def recreate_step(plan_info, step_meta):
    return ExecutionStep(
        key=step_meta.key,
        step_inputs=[
            recreate_step_input(plan_info, step_input_meta)
            for step_input_meta in step_meta.step_input_metas
        ],
        step_outputs=[
            recreate_step_output(plan_info, step_output_meta)
            for step_output_meta in step_meta.step_output_metas
        ],
        compute_fn=recreate_compute_fn(plan_info, step_meta),
        tag=step_meta.tag,
        solid=plan_info.pipeline.solid_named(step_meta.solid_name),
    )


def recreate_execution_steps(pipeline_def, typed_environment, execution_plan_data):
    with yield_context(pipeline_def, typed_environment) as context:
        plan_info = ExecutionPlanInfo(context, pipeline_def, typed_environment)

        execution_plan_meta = ExecutionPlanMeta.create(execution_plan_data)

        steps = []
        for step_meta in execution_plan_meta.step_metas:
            steps.append(recreate_step(plan_info, step_meta))

        return steps


def recreate_execution_plan(pipeline_def, typed_enviroment, execution_plan_data):
    return create_execution_plan_from_steps(
        recreate_execution_steps(
            pipeline_def,
            typed_enviroment,
            execution_plan_data,
        )
    )
