class MockDatabase:
    def execute(self, query: str):
        pass


def get_database_connection():
    return MockDatabase()


# start_marker
import dagster as dg


@dg.op
def create_table_1():
    get_database_connection().execute(
        "create table_1 as select * from some_source_table"
    )


@dg.op(ins={"start": dg.In(dg.Nothing)})
def create_table_2():
    get_database_connection().execute("create table_2 as select * from table_1")


@dg.graph
def nothing_dependency():
    create_table_2(start=create_table_1())


# end_marker
