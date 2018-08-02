import dagster
from dagster import config
from dagster.core.definitions import SolidDefinition
from dagster.utils.compatability import (
    create_custom_source_input, create_single_materialization_output
)
from dagster.core.execution import output_single_solid


def test_iterator_solid():
    def input_fn(_context, _arg_dict):
        yield 1
        yield 2

    some_input = create_custom_source_input(
        name='iter_numbers',
        source_fn=input_fn,
        argument_def_dict={},
    )

    def transform_fn(_context, args):
        for value in args['iter_numbers']:
            yield value + 1

    output_spot = {}

    def materialization_fn(_context, _arg_dict, data_iter):
        output_spot['list'] = list(data_iter)

        # in a real case we would iterate over
        # and stream to disk

    custom_output = create_single_materialization_output(
        name='CUSTOM',
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
        dagster.ExecutionContext(),
        iterable_solid,
        environment=config.Environment(
            sources={'some_node': {
                'iter_numbers': config.Source('CUSTOM', {})
            }}
        ),
        name='CUSTOM',
        arg_dict={}
    )

    assert output_spot['list'] == [2, 3]
