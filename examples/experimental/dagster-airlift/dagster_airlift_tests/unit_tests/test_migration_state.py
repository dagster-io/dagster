from pathlib import Path

import pytest
import yaml
from dagster_airlift.core import load_migration_state_from_yaml
from dagster_airlift.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
    MigrationStateParsingError,
    TaskMigrationState,
)


def test_migration_state() -> None:
    """Test that we can load a migration state from a yaml file, and that errors are handled in a reasonable way."""
    # First test a valid migration directory with two files.
    valid_migration_file = Path(__file__).parent / "migration_state_yamls" / "valid"
    migration_state = load_migration_state_from_yaml(valid_migration_file)
    assert isinstance(migration_state, AirflowMigrationState)
    assert migration_state == AirflowMigrationState(
        dags={
            "first": DagMigrationState(
                tasks={
                    "first_task": TaskMigrationState(task_id="first_task", migrated=True),
                    "second_task": TaskMigrationState(task_id="second_task", migrated=False),
                    "third_task": TaskMigrationState(task_id="third_task", migrated=True),
                }
            ),
            "second": DagMigrationState(
                tasks={
                    "some_task": TaskMigrationState("some_task", migrated=True),
                    "other_task": TaskMigrationState("other_task", migrated=False),
                }
            ),
        }
    )

    # Test various incorrect yaml dirs.
    incorrect_dirs = ["empty_file", "nonexistent_dir", "extra_key", "nonsense"]
    for incorrect_dir in incorrect_dirs:
        incorrect_migration_file = Path(__file__).parent / "migration_state_yamls" / incorrect_dir
        with pytest.raises(MigrationStateParsingError, match="Error parsing migration yaml"):
            load_migration_state_from_yaml(incorrect_migration_file)


def test_migration_state_from_yaml() -> None:
    migration_dict = yaml.safe_load("""
tasks:
  - id: load_raw_customers
    migrated: False
  - id: build_dbt_models
    migrated: False
  - id: export_customers
    migrated: True 
 """)

    migration_state = DagMigrationState.from_dict(migration_dict)
    assert migration_state.is_task_migrated("load_raw_customers") is False
    assert migration_state.is_task_migrated("build_dbt_models") is False
    assert migration_state.is_task_migrated("export_customers") is True
