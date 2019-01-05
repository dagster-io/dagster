import pytest

from dagster import (
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    check,
    lambda_solid,
)

from dagster.core.system_config.objects import EnvironmentConfig

from dagster.core.execution import create_execution_plan

from dagster.core.execution_plan.create import (
    ExecutionPlanInfo,
    create_execution_plan_core,
    create_execution_plan_from_steps,
)

from dagster.core.execution_plan.objects import ExecutionStep, StepTag

from dagster.core.execution_plan.simple_engine import execute_step

from dagster.utils.test import create_test_runtime_execution_context


def silencing_default_context():
    return {'default': PipelineContextDefinition(context_fn=lambda *_args: ExecutionContext())}


@lambda_solid
def noop():
    return 'foo'


def silencing_pipeline(solids):
    return PipelineDefinition(solids=solids, context_definitions=silencing_default_context())


def test_compute_noop_node_core():
    pipeline = silencing_pipeline(solids=[noop])

    environment = EnvironmentConfig()

    plan = create_execution_plan_core(
        ExecutionPlanInfo(create_test_runtime_execution_context(), pipeline, environment)
    )

    assert len(plan.steps) == 1

    outputs = list(execute_step(plan.steps[0], create_test_runtime_execution_context(), {}))

    assert outputs[0].success_data.value == 'foo'


def test_compute_noop_node():
    pipeline = silencing_pipeline(solids=[noop])

    plan = create_execution_plan(pipeline)

    assert len(plan.steps) == 1
    outputs = list(execute_step(plan.steps[0], create_test_runtime_execution_context(), {}))

    assert outputs[0].success_data.value == 'foo'


def test_duplicate_steps():
    @lambda_solid
    def foo():
        pass

    with pytest.raises(check.CheckError):
        create_execution_plan_from_steps(
            [
                ExecutionStep(
                    'same_name', [], [], lambda *args, **kwargs: None, StepTag.TRANSFORM, foo
                ),
                ExecutionStep(
                    'same_name', [], [], lambda *args, **kwargs: None, StepTag.TRANSFORM, foo
                ),
            ]
        )
