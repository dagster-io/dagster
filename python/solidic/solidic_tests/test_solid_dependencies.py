import check

from solidic.definitions import (SolidInputDefinition, Solid, SolidOutputTypeDefinition)
from solidic.graph import (create_adjacency_lists, SolidGraph)


def create_dummy_output_def():
    return SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )


def _default_passthrough_transform(*args, **kwargs):
    check.invariant(not args, 'There should be no positional args')
    return list(kwargs.values())[0]


def throw_input_fn(*_args, **_kwargs):
    raise Exception('should not be invoked')


def create_solid_with_deps(name, *solid_deps):
    inputs = [
        SolidInputDefinition(
            solid_dep.name, input_fn=throw_input_fn, argument_def_dict={}, depends_on=solid_dep
        ) for solid_dep in solid_deps
    ]

    return Solid(
        name=name,
        inputs=inputs,
        transform_fn=_default_passthrough_transform,
        output_type_defs=[create_dummy_output_def()],
    )


def create_root_solid(name):
    input_name = name + '_input'
    inp = SolidInputDefinition(
        input_name,
        input_fn=lambda arg_dict: [{name: 'input_set'}],
        argument_def_dict={},
    )

    return Solid(
        name=name,
        inputs=[inp],
        transform_fn=_default_passthrough_transform,
        output_type_defs=[create_dummy_output_def()]
    )


def test_empty_adjaceny_lists():
    forward_edges, backwards_edges = create_adjacency_lists([create_root_solid('a_node')])
    assert forward_edges == {'a_node': set()}
    assert backwards_edges == {'a_node': set()}


def test_single_dep_adjacency_lists():
    # A <-- B
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b])

    assert forward_edges == {'A': {'B'}, 'B': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set()}


def test_diamond_deps_adjaceny_lists():
    # A <-- (B, C) <-- D

    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b, node_c, node_d])
    assert forward_edges == {'A': {'B', 'C'}, 'B': {'D'}, 'C': {'D'}, 'D': set()}
    assert backwards_edges == {'D': {'B', 'C'}, 'B': {'A'}, 'C': {'A'}, 'A': set()}


def test_disconnected_graphs_adjaceny_lists():
    # A <-- B
    # C <-- D
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)

    node_c = create_root_solid('C')
    node_d = create_solid_with_deps('D', node_c)

    forward_edges, backwards_edges = create_adjacency_lists([node_a, node_b, node_c, node_d])
    assert forward_edges == {'A': {'B'}, 'B': set(), 'C': {'D'}, 'D': set()}
    assert backwards_edges == {'B': {'A'}, 'A': set(), 'D': {'C'}, 'C': set()}


def test_diamond_toposort():

    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)

    graph = SolidGraph([node_d, node_c, node_b, node_a])
    assert graph.topological_order == ['A', 'B', 'C', 'D']
