from dagster_examples.stocks.repository import partitioning_tutorial


def test_basic():
    repo = partitioning_tutorial
    assert len(repo.get_all_pipelines()) == 1
    assert len(repo.schedule_defs) == 1
    assert len(repo.partition_set_defs) == 1
