import dagster as dg

from databricks_delta.definitions import defs  # type: ignore[import-not-found]


def test_definitions_load():
    assert isinstance(defs, dg.Definitions)


def test_resources_exist():
    repo = defs.get_repository_def()
    resources = set(repo.get_top_level_resources().keys())
    assert "databricks" in resources
    assert "delta_storage" in resources
