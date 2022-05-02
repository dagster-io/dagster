# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis
from dagster import ResourceDefinition, graph, job


# start_resource_example
from dagster import resource


class ExternalCerealFetcher:
    def fetch_new_cereals(self, start_ts, end_ts):
        pass


@resource
def cereal_fetcher(init_context):
    return ExternalCerealFetcher()


# end_resource_example

# start_op_with_resources_example
from dagster import op

CREATE_TABLE_1_QUERY = "create table_1 as select * from table_0"


@op(required_resource_keys={"database"})
def op_requires_resources(context):
    context.resources.database.execute_query(CREATE_TABLE_1_QUERY)


# end_op_with_resources_example

# start_resource_testing
from dagster import resource


@resource
def my_resource(_):
    return "foo"


def test_my_resource():
    assert my_resource(None) == "foo"


# end_resource_testing

# start_resource_testing_with_context
from dagster import build_init_resource_context, resource


@resource(required_resource_keys={"foo"}, config_schema={"bar": str})
def my_resource_requires_context(init_context):
    return init_context.resources.foo, init_context.resource_config["bar"]


def test_my_resource_with_context():
    init_context = build_init_resource_context(
        resources={"foo": "foo_str"}, config={"bar": "bar_str"}
    )
    assert my_resource_requires_context(init_context) == ("foo_str", "bar_str")


# end_resource_testing_with_context

# start_test_cm_resource
from contextlib import contextmanager
from dagster import resource


@resource
@contextmanager
def my_cm_resource(_):
    yield "foo"


def test_cm_resource():
    with my_cm_resource(None) as initialized_resource:
        assert initialized_resource == "foo"


# end_test_cm_resource

database_resource = ResourceDefinition.mock_resource()
database_resource_a = ResourceDefinition.mock_resource()
database_resource_b = ResourceDefinition.mock_resource()


# start_job_example
from dagster import job


@job(resource_defs={"database": database_resource})
def do_database_stuff_job():
    op_requires_resources()


# end_job_example

# start_graph_example
from dagster import graph


@graph
def do_database_stuff():
    op_requires_resources()


do_database_stuff_prod = do_database_stuff.to_job(
    resource_defs={"database": database_resource_a}
)
do_database_stuff_dev = do_database_stuff.to_job(
    resource_defs={"database": database_resource_b}
)


# end_graph_example


class Client:
    def __init__(self, _user, _password):
        pass


# start_resource_dep_example
from dagster import resource


@resource
def credentials():
    return ("bad_username", "easy_password")


@resource(required_resource_keys={"credentials"})
def client(init_context):
    username, password = init_context.resources.credentials
    return Client(username, password)


# end_resource_dep_example

# start_resource_dep_op
from dagster import graph, op


@op(required_resource_keys={"client"})
def get_client(context):
    return context.resources.client


# end_resource_dep_op

# start_resource_dep_job
@job(resource_defs={"credentials": credentials, "client": client})
def connect():
    get_client()


# end_resource_dep_job


# start_resource_config
class DatabaseConnection:
    def __init__(self, connection: str):
        self.connection = connection


@resource(config_schema={"connection": str})
def db_resource(init_context):
    connection = init_context.resource_config["connection"]
    return DatabaseConnection(connection)


# end_resource_config


def get_db_connection():
    return "foo"


def cleanup_db_connection(_db_conn):
    pass


# start_cm_resource
@resource
@contextmanager
def db_connection():
    try:
        db_conn = get_db_connection()
        yield db_conn
    finally:
        cleanup_db_connection(db_conn)


# end_cm_resource

# pylint: disable=unused-variable
# start_cm_resource_op
@op(required_resource_keys={"db_connection"})
def use_db_connection(context):
    db_conn = context.resources.db_connection
    ...


# end_cm_resource_op


@job
def the_job():
    ...


def get_the_db_connection(_):
    ...


# pylint: disable=unused-variable,reimported
# start_build_resources_example
from dagster import resource, build_resources


@resource
def the_credentials():
    ...


@resource(required_resource_keys={"credentials"})
def the_db_connection(init_context):
    get_the_db_connection(init_context.resources.credentials)


def uses_db_connection():
    with build_resources(
        {"db_connection": the_db_connection, "credentials": the_credentials}
    ) as resources:
        conn = resources.db_connection
        ...


# end_build_resources_example
