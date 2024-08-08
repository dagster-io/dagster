from pathlib import Path

import pytest
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster_airlift.core import load_migration_state_from_yaml
from dagster_airlift.core.migration_state import (
    AirflowMigrationState,
    DagMigrationState,
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
                    "first_task": TaskMigrationState(migrated=True),
                    "second_task": TaskMigrationState(migrated=False),
                    "third_task": TaskMigrationState(migrated=True),
                }
            ),
            "second": DagMigrationState(
                tasks={
                    "some_task": TaskMigrationState(migrated=True),
                    "other_task": TaskMigrationState(migrated=False),
                }
            ),
        }
    )

    # Test various incorrect yaml dirs.
    incorrect_dirs = ["empty_file", "nonexistent_dir", "extra_key", "nonsense"]
    for incorrect_dir in incorrect_dirs:
        incorrect_migration_file = Path(__file__).parent / "migration_state_yamls" / incorrect_dir
        with pytest.raises(DagsterInvalidDefinitionError, match="Error parsing migration yaml"):
            load_migration_state_from_yaml(incorrect_migration_file)
