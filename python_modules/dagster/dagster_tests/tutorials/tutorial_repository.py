from dagster import RepositoryDefinition

from dagster.dagster_examples.tutorials.test_intro_tutorial_part_one import define_pipeline as define_part_one_pipeline
# from .test_intro_tutorial_part_one import define_pipeline as define_part_one_pipeline


def define_repository():
    return RepositoryDefinition(
        name='tutorial_repository',
        pipeline_dict={
            'part_one_pipeline': define_part_one_pipeline,
        },
    )
