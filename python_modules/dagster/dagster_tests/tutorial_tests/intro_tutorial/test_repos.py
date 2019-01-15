from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.repos import define_repo


def test_define_repo():
    repo = define_repo()
    assert repo.name == 'demo_repository'
    assert repo.has_pipeline('repo_demo_pipeline')
    result = execute_pipeline(repo.get_pipeline('repo_demo_pipeline'))
    assert result.success
