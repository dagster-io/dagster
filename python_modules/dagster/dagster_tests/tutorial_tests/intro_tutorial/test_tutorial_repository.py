from dagster.tutorials.intro_tutorial.tutorial_repository import define_repository


def test_intro_tutorial_repository():
    repo = define_repository()
    assert repo
    assert repo.get_all_pipelines()
