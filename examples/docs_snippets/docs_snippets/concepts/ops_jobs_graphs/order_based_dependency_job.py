# pylint: disable=unused-argument, no-value-for-parameter


class MockDatabase:
    def execute(self, query: str):
        pass


def get_database_connection():
    return MockDatabase()


# start_marker
from dagster import In, Nothing, job, op


@op
def create_table_1():
    get_database_connection().execute(
        "create table_1 as select * from some_source_table"
    )


@op(ins={"start": In(Nothing)})
def create_table_2():
    get_database_connection().execute("create table_2 as select * from table_1")


@job
def nothing_dependency():
    create_table_2(start=create_table_1())


# end_marker
