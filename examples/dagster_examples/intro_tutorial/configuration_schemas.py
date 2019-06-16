# pylint: disable=no-value-for-parameter

import collections

from dagster import Field, Int, lambda_solid, solid, pipeline, as_dagster_type

Counter = as_dagster_type(collections.Counter)


@solid(config={'factor': Field(Int)})
def multiply_the_word(context, word: str) -> str:
    return word * context.solid_config['factor']


@lambda_solid
def count_letters(word: str) -> Counter:
    return collections.Counter(word)


@pipeline
def configuration_schema_pipeline(_):
    return count_letters(multiply_the_word())
