from dagster import RepositoryDefinition

from toys.error_monster import define_error_monster_pipeline
from toys.sleepy import define_sleepy_pipeline
from toys.log_spew import define_spew_pipeline
from toys.many_events import define_many_events_pipeline


def define_repo(repo_config=None):
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_dict={
            'sleepy': define_sleepy_pipeline,
            'error_monster': define_error_monster_pipeline,
            'log_spew': define_spew_pipeline,
            'many_events': define_many_events_pipeline,
        },
        repo_config=repo_config,
    )
