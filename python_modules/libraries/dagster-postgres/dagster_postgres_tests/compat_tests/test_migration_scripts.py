import os
from filecmp import cmpfiles

from dagster.utils import file_relative_path


# For postgres we must ensure that all the different stores have the same migration
# scripts because they may share the database and alembic requires exhaustive
# history for each individual store.
def test_all_migration_scripts_samesies():
    base_dir = file_relative_path(__file__, "../../dagster_postgres/")

    def _get_migration_files(store):
        event_log_path = os.path.join(base_dir, store, "alembic", "versions")
        return list(filter(lambda p: p.endswith(".py"), os.listdir(event_log_path)))

    def _get_versions_path(store):
        return os.path.join(base_dir, store, "alembic", "versions")

    migration_files = _get_migration_files("event_log")

    other_stores = ["run_storage", "schedule_storage"]

    for other_store in other_stores:
        # check that same set of files exists in each store
        assert set(_get_migration_files(other_store)) == set(migration_files)

    for other_store in other_stores:
        match, _mismatch, _errors = cmpfiles(
            _get_versions_path("event_log"),
            _get_versions_path(other_store),
            migration_files,
        )

        assert set(match) == set(migration_files)
