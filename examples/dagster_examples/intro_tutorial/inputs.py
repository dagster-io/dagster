from dagster import String, execute_pipeline, pipeline, solid


@solid
def add_hello_to_word(_, word):
    return 'Hello, ' + word + '!'


@pipeline
def hello_inputs_pipeline():
    add_hello_to_word()


def execute_with_another_world():
    return execute_pipeline(
        hello_inputs_pipeline,
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


@solid
def add_hello_to_word_typed(_, word: String) -> String:
    return 'Hello, ' + word + '!'


@pipeline
def hello_typed_inputs_pipeline():
    add_hello_to_word_typed()
