from dagster import (
    ExecutionContext,
    PipelineContextDefinition,
    PipelineDefinition,
    config,
    solid,
    OutputDefinition,
)

from dagster.core.execution import (DagsterEnv, ExecutionGraph)
from dagster.core.compute_nodes import create_compute_node_graph_from_env
from dagster.core.graph import ExecutionGraph


def silencing_default_context():
    return {
        'default':
        PipelineContextDefinition(
            argument_def_dict={},
            context_fn=lambda _pipeline, _args: ExecutionContext(),
        )
    }


@solid(name='noop', inputs=[], outputs=[OutputDefinition()])
def noop_solid():
    return 'foo'


def silencing_pipeline(solids):
    return PipelineDefinition(solids=solids, context_definitions=silencing_default_context())


def test_compute_noop_node():
    pipeline = silencing_pipeline(solids=[
        noop_solid,
    ])

    environment = config.Environment()

    env = DagsterEnv(ExecutionGraph.from_pipeline(pipeline), environment)
    compute_node_graph = create_compute_node_graph_from_env(
        ExecutionGraph.from_pipeline(pipeline),
        env,
    )

    assert len(compute_node_graph.nodes) == 1

    outputs = list(compute_node_graph.nodes[0].execute(ExecutionContext(), {}))

    assert outputs[0].success_data.value == 'foo'
