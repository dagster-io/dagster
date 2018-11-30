from dagster import (
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    config,
    lambda_solid,
)

from dagster.core.execution import (
    create_execution_plan,
    ExecutionPlanInfo,
    RuntimeExecutionContext,
)

from dagster.core.definitions import ExecutionGraph

from dagster.core.execution_plan import create_execution_plan_core

from dagster.utils.test import create_test_runtime_execution_context


def silencing_default_context():
    return {'default': PipelineContextDefinition(context_fn=lambda *_args: ExecutionContext(), )}


@lambda_solid
def noop():
    return 'foo'


def silencing_pipeline(solids):
    return PipelineDefinition(solids=solids, context_definitions=silencing_default_context())


def test_compute_noop_node_core():
    pipeline = silencing_pipeline(solids=[
        noop,
    ])

    environment = config.Environment()

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    plan = create_execution_plan_core(
        ExecutionPlanInfo(
            create_test_runtime_execution_context(),
            execution_graph,
            environment,
        ),
    )

    assert len(plan.steps) == 1

    outputs = list(plan.steps[0].execute(create_test_runtime_execution_context(), {}))

    assert outputs[0].success_data.value == 'foo'


def test_compute_noop_node():
    pipeline = silencing_pipeline(solids=[
        noop,
    ])

    plan = create_execution_plan(pipeline)

    assert len(plan.steps) == 1
    outputs = list(plan.steps[0].execute(create_test_runtime_execution_context(), {}))

    assert outputs[0].success_data.value == 'foo'
