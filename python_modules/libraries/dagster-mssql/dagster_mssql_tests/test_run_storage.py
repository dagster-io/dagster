from urllib.parse import urlparse

import pytest
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster_mssql.run_storage import MSSQLRunStorage
from dagster_shared.yaml_utils import safe_load_yaml

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.run_storage import TestRunStorage

TestRunStorage.__test__ = False


class TestMSSQLRunStorage(TestRunStorage):
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
        MSSQLRunStorage.create_clean_storage(conn_string)

        with instance_for_test(
            overrides={"storage": {"mssql": {"mssql_url": conn_string}}}
        ) as instance:
            yield instance

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, instance):
        run_storage = instance.run_storage
        assert isinstance(run_storage, MSSQLRunStorage)
        return run_storage

    def test_load_from_config(self, conn_string):
        parse_result = urlparse(conn_string)
        hostname = parse_result.hostname  # can be custom set in the BK env
        port = parse_result.port

        url_cfg = f"""
          run_storage:
            module: dagster_mssql.run_storage
            class: MSSQLRunStorage
            config:
              mssql_url: "{conn_string}"
        """

        explicit_cfg = f"""
          run_storage:
            module: dagster_mssql.run_storage
            class: MSSQLRunStorage
            config:
              mssql_db:
                username: sa
                password: "Dagster!Passw0rd"
                hostname: {hostname}
                db_name: test
                port: {port}
                params:
                  TrustServerCertificate: "yes"
        """

        with environ({"TEST_MSSQL_PASSWORD": "Dagster!Passw0rd"}):
            env_cfg = f"""
            run_storage:
              module: dagster_mssql.run_storage
              class: MSSQLRunStorage
              config:
                mssql_db:
                  username: sa
                  password:
                    env: TEST_MSSQL_PASSWORD
                  hostname: {hostname}
                  db_name: test
                  port: {port}
                  params:
                    TrustServerCertificate: "yes"
            """

            with instance_for_test(overrides=safe_load_yaml(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=safe_load_yaml(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.mssql_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                        == from_explicit_instance._run_storage.mssql_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                    )
                with instance_for_test(overrides=safe_load_yaml(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.mssql_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                        == from_env_instance._run_storage.mssql_url  # noqa: SLF001  # ty: ignore[unresolved-attribute]
                    )
