# pylint: disable=unused-argument, no-value-for-parameter


class MockDatabase:
    def execute(self, query: str):
        pass


def get_database_connection():
    return MockDatabase()


# start_marker
from dagster import InputDefinition, Nothing, pipeline, solid


@solid
def create_table_1():
    get_database_connection().execute("create table_1 as select * from some_source_table")


@solid(input_defs=[InputDefinition("start", Nothing)])
def create_table_2():
    get_database_connection().execute("create table_2 as select * from table_1")


@pipeline
def nothing_dependency_pipeline():
    create_table_2(start=create_table_1())


# end_marker
