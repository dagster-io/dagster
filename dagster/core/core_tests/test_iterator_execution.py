import dagster
from dagster.core.definitions import (
    SolidDefinition, create_single_materialization_output, create_single_source_input
)
from dagster.core.execution import (output_single_solid, create_single_solid_env_from_arg_dicts)


def test_iterator_solid():
    def input_fn(context, arg_dict):
        yield 1
        yield 2

    some_input = create_single_source_input(
        name='iter_numbers',
        source_fn=input_fn,
        argument_def_dict={},
    )

    def transform_fn(context, args):
        for value in args['iter_numbers']:
            yield value + 1

    output_spot = {}

    def materialization_fn(context, arg_dict, data_iter):
        output_spot['list'] = list(data_iter)

        # in a real case we would iterate over
        # and stream to disk

    custom_output = create_single_materialization_output(
        materialization_type='CUSTOM',
        materialization_fn=materialization_fn,
        argument_def_dict={},
    )

    iterable_solid = SolidDefinition(
        name='some_node',
        inputs=[some_input],
        transform_fn=transform_fn,
        output=custom_output,
    )

    output_single_solid(
        dagster.context(),
        iterable_solid,
        environment=create_single_solid_env_from_arg_dicts(iterable_solid, {'iter_numbers': {}}),
        materialization_type='CUSTOM',
        arg_dict={}
    )

    assert output_spot['list'] == [2, 3]
