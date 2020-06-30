from dagster import check


class TestPostgresInstance:
    @staticmethod
    def dagster_postgres_installed():
        try:
            import dagster_postgres  # pylint: disable=unused-import
        except ImportError:
            return False
        return True

    @staticmethod
    def get_hostname(env_name='POSTGRES_TEST_DB_HOST'):
        import os

        # In buildkite we get the ip address from this variable (see buildkite code for commentary)
        # Otherwise assume local development and assume localhost
        return os.environ.get(env_name, 'localhost')

    @staticmethod
    def conn_string(**kwargs):
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.utils import get_conn_string  # pylint: disable=import-error

        return get_conn_string(
            **dict(
                dict(
                    username='test',
                    password='test',
                    hostname=TestPostgresInstance.get_hostname(),
                    db_name='test',
                ),
                **kwargs
            )
        )

    @staticmethod
    def clean_run_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.run_storage import PostgresRunStorage  # pylint: disable=import-error

        storage = PostgresRunStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage

    @staticmethod
    def clean_event_log_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.event_log import (  # pylint: disable=import-error
            PostgresEventLogStorage,
        )

        storage = PostgresEventLogStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage

    @staticmethod
    def clean_schedule_storage():
        check.invariant(
            TestPostgresInstance.dagster_postgres_installed(),
            'dagster_postgres must be installed to test with postgres',
        )
        from dagster_postgres.schedule_storage.schedule_storage import (  # pylint: disable=import-error
            PostgresScheduleStorage,
        )

        storage = PostgresScheduleStorage.create_clean_storage(TestPostgresInstance.conn_string())
        assert storage
        return storage
