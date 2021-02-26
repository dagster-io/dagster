from dagster import solid

CREATE_TABLE_1_QUERY = "create table_1 as select * from table_0"
CREATE_TABLE_2_QUERY = "create table_2 as select * from table_1"


@solid(required_resource_keys={"database"})
def generate_table_1(context):
    context.resources.database.execute_query(CREATE_TABLE_1_QUERY)


@solid(required_resource_keys={"database"})
def generate_table_2(context):
    context.resources.database.execute_query(CREATE_TABLE_2_QUERY)
