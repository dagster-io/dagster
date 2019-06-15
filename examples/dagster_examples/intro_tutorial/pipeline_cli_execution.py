# pylint: disable=no-value-for-parameter

from collections import defaultdict

from dagster import pipeline, Field, Int, RepositoryDefinition, lambda_solid, solid


@solid(config={'factor': Field(Int)})
def multiply_the_word(context, word: str) -> str:
    return word * context.solid_config['factor']


@lambda_solid
def count_letters(word: str):  # TODO type return as dict?
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@pipeline
def demo_execution_pipeline(_):
    return count_letters(multiply_the_word())


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo',
        pipeline_dict={'demo_execution_pipeline': demo_execution_pipeline},
    )
