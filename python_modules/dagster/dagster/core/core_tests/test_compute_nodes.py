from dagster import (
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    config,
    lambda_solid,
)

from dagster.core.execution import (
    ComputeNodeExecutionInfo,
)

from dagster.core.definitions import ExecutionGraph

from dagster.core.compute_nodes import create_compute_node_graph


def silencing_default_context():
    return {'default': PipelineContextDefinition(context_fn=lambda *_args: ExecutionContext(), )}


@lambda_solid
def noop():
    return 'foo'


def silencing_pipeline(solids):
    return PipelineDefinition(solids=solids, context_definitions=silencing_default_context())


def test_compute_noop_node():
    pipeline = silencing_pipeline(solids=[
        noop,
    ])

    environment = config.Environment()

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    compute_node_graph = create_compute_node_graph(
        ComputeNodeExecutionInfo(
            ExecutionContext(),
            execution_graph,
            environment,
        ),
    )

    assert len(compute_node_graph.nodes) == 1

    outputs = list(compute_node_graph.nodes[0].execute(ExecutionContext(), {}))

    assert outputs[0].success_data.value == 'foo'
