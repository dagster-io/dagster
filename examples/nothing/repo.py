from dagster import InputDefinition, Nothing, pipeline, repository, solid


def get_database_connection():
    class Database:
        def execute(self, query):
            pass

    return Database()


@solid
def create_table_1(_) -> Nothing:
    get_database_connection().execute("create table_1 as select * from some_source_table")


@solid(input_defs=[InputDefinition("start", Nothing)])
def create_table_2(_):
    get_database_connection().execute("create table_2 as select * from table_1")


@pipeline
def my_pipeline():
    create_table_2(create_table_1())


@repository
def nothing_example_repository():
    return [my_pipeline]
