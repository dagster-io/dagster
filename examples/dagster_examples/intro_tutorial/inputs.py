# pylint: disable=no-value-for-parameter
from dagster import execute_pipeline, lambda_solid, pipeline, String


@lambda_solid
def add_hello_to_word(word):
    return 'Hello, ' + word + '!'


@pipeline
def hello_inputs_pipeline(_):
    add_hello_to_word()


def define_hello_inputs_pipeline():
    return hello_inputs_pipeline


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


@lambda_solid
def add_hello_to_word_typed(word: String) -> String:
    return 'Hello, ' + word + '!'


@pipeline
def hello_typed_inputs_pipeline(_):
    add_hello_to_word_typed()


def define_hello_typed_inputs_pipeline():
    return hello_typed_inputs_pipeline
