from dagster import RepositoryDefinition

from .pipelines import generate_training_set_and_train_model


def define_repo():
    return RepositoryDefinition(
        name='bay_bikes_demo',
        pipeline_dict={
            'generate_training_set_and_train_model': lambda: generate_training_set_and_train_model
        },
    )
