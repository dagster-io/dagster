from dagster_examples.intro_tutorial.repos import define_repo
from dagster_examples.intro_tutorial.scheduler import scheduled_cereal_repository

from dagster import execute_pipeline
from dagster.utils import pushd, script_relative_path


def test_define_repo():
    repo = define_repo()
    assert repo.name == 'hello_cereal_repository'
    assert repo.has_pipeline('hello_cereal_pipeline')
    with pushd(script_relative_path('../../dagster_examples/intro_tutorial/')):
        result = execute_pipeline(repo.get_pipeline('hello_cereal_pipeline'))
    assert result.success


def test_define_scheduler_repo():
    repo = scheduled_cereal_repository()
    assert repo.name == 'scheduled_cereal'
    assert repo.has_pipeline('scheduled_cereal_pipeline')
    with pushd(script_relative_path('../../dagster_examples/intro_tutorial/')):
        result = execute_pipeline(repo.get_pipeline('scheduled_cereal_pipeline'))
    assert result.success
