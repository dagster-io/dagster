import collections

from dagster import Any, Field, Int, pipeline, solid


@solid(config={'factor': Field(Any)})
def multiply_the_word(context, word: str) -> str:
    return word * context.solid_config['factor']


@solid
def count_letters(_, word: str) -> collections.Counter:
    return collections.Counter(word)


@pipeline
def configuration_schema_pipeline():
    return count_letters(multiply_the_word())


@solid(config={'factor': Field(Int)})
def typed_multiply_the_word(context, word: str) -> str:
    return word * context.solid_config['factor']


@pipeline
def typed_configuration_schema_pipeline():
    return count_letters(typed_multiply_the_word())
