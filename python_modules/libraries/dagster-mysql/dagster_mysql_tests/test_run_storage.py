from urllib.parse import urlparse

import pytest
import yaml
from dagster._core.test_utils import ensure_dagster_tests_import, environ, instance_for_test
from dagster_mysql.run_storage import MySQLRunStorage

ensure_dagster_tests_import()
from dagster_tests.storage_tests.utils.run_storage import TestRunStorage

TestRunStorage.__test__ = False


class TestMySQLRunStorage(TestRunStorage):
    __test__ = True
    # TestMySQLRunStorage::test_backfill_tags_filtering_multiple_results

    def supports_backfill_tags_filtering_queries(self):
        return True

    def supports_backfill_job_name_filtering_queries(self):
        return True

    def supports_backfill_id_filtering_queries(self):
        return True

    def supports_backfills_count(self):
        return True

    @pytest.fixture(name="instance", scope="function")
    def instance(self, conn_string):
        MySQLRunStorage.create_clean_storage(conn_string)

        with instance_for_test(
            overrides={"storage": {"mysql": {"mysql_url": conn_string}}}
        ) as instance:
            yield instance

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, instance):
        run_storage = instance.run_storage
        assert isinstance(run_storage, MySQLRunStorage)
        return run_storage

    def test_load_from_config(self, conn_string):
        parse_result = urlparse(conn_string)
        hostname = parse_result.hostname  # can be custom set in the BK env
        port = (
            parse_result.port
        )  # can be different, based on the backcompat mysql version or latest mysql version

        url_cfg = f"""
          run_storage:
            module: dagster_mysql.run_storage
            class: MySQLRunStorage
            config:
              mysql_url: mysql+mysqlconnector://test:test@{hostname}:{port}/test
        """

        explicit_cfg = f"""
          run_storage:
            module: dagster_mysql.run_storage
            class: MySQLRunStorage
            config:
              mysql_db:
                username: test
                password: test
                hostname: {hostname}
                db_name: test
                port: {port}
        """

        with environ({"TEST_MYSQL_PASSWORD": "test"}):
            env_cfg = f"""
            run_storage:
              module: dagster_mysql.run_storage
              class: MySQLRunStorage
              config:
                mysql_db:
                  username: test
                  password:
                    env: TEST_MYSQL_PASSWORD
                  hostname: {hostname}
                  db_name: test
                  port: {port}
            """

            with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=yaml.safe_load(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                        == from_explicit_instance._run_storage.mysql_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                    )
                with instance_for_test(overrides=yaml.safe_load(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                        == from_env_instance._run_storage.mysql_url  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                    )
