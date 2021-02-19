import pytest
import yaml
from dagster.core.test_utils import environ, instance_for_test
from dagster_mysql.run_storage import MySQLRunStorage
from dagster_tests.core_tests.storage_tests.utils.run_storage import TestRunStorage

TestRunStorage.__test__ = False


class TestMySQLRunStorage(TestRunStorage):
    __test__ = True

    @pytest.fixture(scope="function", name="storage")
    def run_storage(self, conn_string):  # pylint: disable=arguments-differ
        storage = MySQLRunStorage.create_clean_storage(conn_string)
        assert storage
        return storage

    def test_load_from_config(self, hostname):
        url_cfg = """
          run_storage:
            module: dagster_mysql.run_storage
            class: MySQLRunStorage
            config:
              mysql_url: mysql+mysqlconnector://test:test@{hostname}:3306/test
        """.format(
            hostname=hostname
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
        """.format(
            hostname=hostname
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
            """.format(
                hostname=hostname
            )

            # pylint: disable=protected-access
            with instance_for_test(overrides=yaml.safe_load(url_cfg)) as from_url_instance:
                with instance_for_test(
                    overrides=yaml.safe_load(explicit_cfg)
                ) as from_explicit_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url
                        == from_explicit_instance._run_storage.mysql_url
                    )
                with instance_for_test(overrides=yaml.safe_load(env_cfg)) as from_env_instance:
                    assert (
                        from_url_instance._run_storage.mysql_url
                        == from_env_instance._run_storage.mysql_url
                    )
