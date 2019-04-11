from dagster import (
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    types,
)


@lambda_solid(inputs=[InputDefinition('word')])
def add_hello_to_word(word):
    return 'Hello, ' + word + '!'


def define_hello_inputs_pipeline():
    return PipelineDefinition(name='hello_inputs', solids=[add_hello_to_word])


def execute_with_another_world():
    return execute_pipeline(
        define_hello_inputs_pipeline(),
        # This entire dictionary is known as the 'environment'.
        # It has many sections.
        {
            # This is the 'solids' section
            'solids': {
                # Configuration for the add_hello_to_word solid
                'add_hello_to_word': {'inputs': {'word': {'value': 'Mars'}}}
            }
        },
    )


@lambda_solid(inputs=[InputDefinition('word', types.String)], output=OutputDefinition(types.String))
def add_hello_to_word_typed(word):
    return 'Hello, ' + word + '!'


def define_hello_typed_inputs_pipeline():
    return PipelineDefinition(name='hello_typed_inputs', solids=[add_hello_to_word_typed])
