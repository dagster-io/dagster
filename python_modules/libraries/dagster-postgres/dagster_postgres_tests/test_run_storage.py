import pytest
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_shared.yaml_utils import safe_load_yaml

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.run_storage import TestRunStorage


class TestPostgresRunStorage(TestRunStorage):
    __test__ = True

    def supports_backfill_tags_filtering_queries(self) -> bool:
        return True

    def supports_backfill_job_name_filtering_queries(self) -> bool:
        return True

    def supports_backfill_id_filtering_queries(self) -> bool:
        return True

    def supports_backfills_count(self) -> bool:
        return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self, conn_string):
        PostgresRunStorage.create_clean_storage(conn_string)

        with instance_for_test(
            overrides={"storage": {"postgres": {"postgres_url": conn_string}}}
        ) as instance:
            yield instance

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, instance):
        storage = instance.run_storage
        assert isinstance(storage, PostgresRunStorage)
        yield storage

    def test_load_from_config(self, hostname):
        url_cfg = f"""
          run_storage:
            module: dagster_postgres.run_storage
            class: PostgresRunStorage
            config:
              postgres_url: postgresql://test:test@{hostname}:5432/test?fallback_application_name=dagster&connect_timeout=15
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

            with instance_for_test(overrides=safe_load_yaml(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=safe_load_yaml(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                        == from_explicit_instance._run_storage.postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                    )
                with instance_for_test(overrides=safe_load_yaml(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                        == from_env_instance._run_storage.postgres_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                    )
