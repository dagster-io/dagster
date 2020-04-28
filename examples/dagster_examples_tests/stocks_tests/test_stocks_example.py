from dagster_examples.stocks.repository import define_repo


def test_basic():
    repo = define_repo()
    assert len(repo.get_all_pipelines()) == 1
    assert len(repo.schedule_defs) == 1
    assert len(repo.partition_set_defs) == 1
