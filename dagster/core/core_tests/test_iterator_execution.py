import dagster
from dagster.core.definitions import (Solid, InputDefinition, OutputDefinition)
from dagster.core.execution import output_single_solid


def test_iterator_solid():
    def input_fn(context, arg_dict):
        yield 1
        yield 2

    some_input = InputDefinition(
        name='iter_numbers',
        input_fn=input_fn,
        argument_def_dict={},
    )

    def transform_fn(iter_numbers):
        for value in iter_numbers:
            yield value + 1

    output_spot = {}

    def output_fn(data_iter, context, arg_dict):
        output_spot['list'] = list(data_iter)

        # in a real case we would iterate over
        # and stream to disk

    custom_output = OutputDefinition(
        name='CUSTOM',
        output_fn=output_fn,
        argument_def_dict={},
    )

    iterable_solid = Solid(
        name='some_node',
        inputs=[some_input],
        transform_fn=transform_fn,
        outputs=[custom_output],
    )

    output_single_solid(
        dagster.context(),
        iterable_solid,
        input_arg_dicts={'iter_numbers': {}},
        output_type='CUSTOM',
        output_arg_dict={}
    )

    assert output_spot['list'] == [2, 3]
