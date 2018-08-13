from dagster import (
    ExecutionContext,
    InputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    config,
    solid,
    source,
    OutputDefinition,
)

from dagster.core.compute_nodes import create_compute_node_graph_from_environment


@solid(name='noop', inputs=[], output=OutputDefinition())
def noop_solid():
    return 'foo'


def silencing_default_context():
    return {
        'default':
        PipelineContextDefinition(
            argument_def_dict={},
            context_fn=lambda _pipeline, _args: ExecutionContext(),
        )
    }


@source()
def load_value_source():
    return 'value'


@solid(
    inputs=[InputDefinition(name='some_input', sources=[load_value_source])],
    output=OutputDefinition()
)
def solid_with_source(some_input):
    return some_input


def silencing_pipeline(solids):
    return PipelineDefinition(solids=solids, context_definitions=silencing_default_context())


def test_compute_noop_node():
    pipeline = silencing_pipeline(solids=[
        noop_solid,
    ])

    environment = config.Environment(sources={})

    compute_node_graph = create_compute_node_graph_from_environment(pipeline, environment)

    assert len(compute_node_graph.nodes) == 1

    context = ExecutionContext()

    outputs = list(compute_node_graph.nodes[0].execute(context, {}))

    assert outputs[0].success_data.value == 'foo'


def test_compute_node_with_source():
    pipeline = silencing_pipeline(solids=[solid_with_source])
    environment = config.Environment(
        sources={
            'solid_with_source': {
                'some_input': config.Source(name='load_value_source', args={})
            }
        }
    )

    compute_node_graph = create_compute_node_graph_from_environment(pipeline, environment)
    assert len(compute_node_graph.nodes) == 2

    context = ExecutionContext()

    node_list = list(compute_node_graph.topological_nodes())

    assert list(node_list[0].execute(context, {}))[0].success_data.value == 'value'
    assert list(node_list[1].execute(context, {'some_input': 'bar'}))[0].success_data.value == 'bar'
