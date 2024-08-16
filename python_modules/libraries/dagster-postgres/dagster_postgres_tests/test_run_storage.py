import pytest
import yaml
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster_postgres.run_storage import PostgresRunStorage

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


class TestPostgresRunStorage(TestRunStorage):
    # TestPostgresRunStorage::test_backfill_created_time_filtering
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, conn_string):
        storage = PostgresRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    def test_load_from_config(self, hostname):
        url_cfg = f"""
          run_storage:
            module: dagster_postgres.run_storage
            class: PostgresRunStorage
            config:
              postgres_url: postgresql://test:test@{hostname}:5432/test
        """

        explicit_cfg = f"""
          run_storage:
            module: dagster_postgres.run_storage
            class: PostgresRunStorage
            config:
              postgres_db:
                username: test
                password: test
                hostname: {hostname}
                db_name: test
        """

        with environ({"TEST_PG_PASSWORD": "test"}):
            env_cfg = f"""
            run_storage:
              module: dagster_postgres.run_storage
              class: PostgresRunStorage
              config:
                postgres_db:
                  username: test
                  password:
                    env: TEST_PG_PASSWORD
                  hostname: {hostname}
                  db_name: test
            """

            with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=yaml.safe_load(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.postgres_url  # noqa: SLF001
                        == from_explicit_instance._run_storage.postgres_url  # noqa: SLF001
                    )
                with instance_for_test(overrides=yaml.safe_load(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.postgres_url  # noqa: SLF001
                        == from_env_instance._run_storage.postgres_url  # noqa: SLF001
                    )
