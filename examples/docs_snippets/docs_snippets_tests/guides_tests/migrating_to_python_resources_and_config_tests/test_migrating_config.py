from docs_snippets.guides.dagster.migrating_to_python_resources_and_config.migrating_config import (
    new_config_schema,
    new_config_schema_and_typed_run_config,
    old_config,
)


def test_old_config() -> None:
    old_config()


def test_new_config_schema() -> None:
    new_config_schema()


def test_new_config_schema_and_typed_run_config() -> None:
    new_config_schema_and_typed_run_config()
