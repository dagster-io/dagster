from docs_snippets.guides.dagster.migrating_to_python_resources_and_config.migrating_config import (
    old_config,
    new_config_schema,
    new_config_schema_and_typed_run_config,
)


def test_old_config() -> None:
    old_config()


def test_new_config_schema() -> None:
    new_config_schema()


def test_new_config_schema_and_typed_run_config() -> None:
    new_config_schema_and_typed_run_config()
