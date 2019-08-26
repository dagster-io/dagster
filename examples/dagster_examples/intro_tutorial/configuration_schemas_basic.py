# pylint: disable=no-value-for-parameter

import collections

from dagster import Any, Field, as_dagster_type, lambda_solid, pipeline, solid

Counter = as_dagster_type(collections.Counter)


@solid(config_field=Field(Any))
def multiply_the_word(context, word: str) -> str:
    return word * context.solid_config['factor']


@lambda_solid
def count_letters(word: str) -> Counter:
    return collections.Counter(word)


@pipeline
def configuration_schema_pipeline():
    return count_letters(multiply_the_word())
