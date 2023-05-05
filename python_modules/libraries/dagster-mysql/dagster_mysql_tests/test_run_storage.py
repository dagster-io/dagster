from urllib.parse import urlparse

import pytest
import yaml
from dagster._core.test_utils import environ, instance_for_test
from dagster_mysql.run_storage import MySQLRunStorage
from dagster_mysql.utils import parse_mysql_version
from dagster_tests.storage_tests.utils.run_storage import TestRunStorage

TestRunStorage.__test__ = False


class TestMySQLRunStorage(TestRunStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, conn_string):
        storage = MySQLRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    def test_load_from_config(self, conn_string):
        parse_result = urlparse(conn_string)
        hostname = parse_result.hostname  # can be custom set in the BK env
        port = (
            parse_result.port
        )  # can be different, based on the backcompat mysql version or latest mysql version

        url_cfg = """
          run_storage:
            module: dagster_mysql.run_storage
            class: MySQLRunStorage
            config:
              mysql_url: mysql+mysqlconnector://test:test@{hostname}:{port}/test
        """.format(
            hostname=hostname,
            port=port,
        )

        explicit_cfg = """
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
        """.format(
            hostname=hostname,
            port=port,
        )

        with environ({"TEST_MYSQL_PASSWORD": "test"}):
            env_cfg = """
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
            """.format(
                hostname=hostname, port=port
            )

            with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=yaml.safe_load(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url  # noqa: SLF001
                        == from_explicit_instance._run_storage.mysql_url  # noqa: SLF001
                    )
                with instance_for_test(overrides=yaml.safe_load(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url  # noqa: SLF001
                        == from_env_instance._run_storage.mysql_url  # noqa: SLF001
                    )


def test_mysql_version(conn_string):
    class FakeNonBucketing(MySQLRunStorage):
        def get_server_version(self):
            # override the server version to make sure the parsing works
            return "5.7.38-log"

    storage = FakeNonBucketing(conn_string)
    assert parse_mysql_version("5.7.38-log") == (5, 7, 38)
    assert not storage.supports_bucket_queries

    class FakeBucketing(MySQLRunStorage):
        def get_server_version(self):
            # override the server version to make sure the parsing works
            return "8.0.31-google"

    storage = FakeBucketing(conn_string)
    assert parse_mysql_version("8.0.31-google") == (8, 0, 31)
    assert storage.supports_bucket_queries
