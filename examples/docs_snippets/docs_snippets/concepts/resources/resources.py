# isort: skip_file
# pylint: disable=unused-argument,reimported,unnecessary-ellipsis
from dagster import ResourceDefinition, graph, job, Definitions


# start_resource_example
from dagster._config.structured_config import Resource


class ExternalCerealFetcher(Resource):
    def fetch_new_cereals(self, start_ts, end_ts):
        pass


# end_resource_example


class DatabaseResource(Resource):
    def execute_query(self, query):
        pass


# start_op_with_resources_example
from dagster import op

CREATE_TABLE_1_QUERY = "create table_1 as select * from table_0"


@op
def op_requires_resources(database: DatabaseResource):
    database.execute_query(CREATE_TABLE_1_QUERY)


# end_op_with_resources_example

# start_resource_testing
from dagster._config.structured_config import Resource


class MyResource(Resource):
    def get_value(self) -> str:
        return "foo"


def test_my_resource():
    assert MyResource().get_value() == "foo"


# end_resource_testing

# start_resource_testing_with_context
from dagster._config.structured_config import Resource


class StringHolderResource(Resource):
    value: str


class MyResourceRequiresAnother(Resource):
    foo: StringHolderResource
    bar: str


def test_my_resource_with_context():
    resource = MyResourceRequiresAnother(foo=StringHolderResource("foo"), bar="bar")
    assert resource.foo.value == "foo"
    assert resource.bar == "bar"


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


do_database_stuff_prod = do_database_stuff.to_job(resource_defs={"database": database_resource_a})
do_database_stuff_dev = do_database_stuff.to_job(resource_defs={"database": database_resource_b})


# end_graph_example


class Client:
    def __init__(self, _user, _password):
        pass


# start_resource_dep_example
from dagster._config.structured_config import Resource


class Credentials(Resource):
    username: str
    password: str


class Client(Resource):
    credentials: Credentials

    def request(self, endpoint: str):
        ...


# end_resource_dep_example

# start_resource_dep_op
from dagster import graph, op


@op
def get_newest_stories(client: Client):
    return client.request("/stories/new")


# end_resource_dep_op


# start_resource_dep_job
credentials = Credentials(username="foo", password="bar")


@job
def connect():
    get_newest_stories()


defs = Definitions(
    jobs=[connect],
    resources={
        "client": Client(credentials=credentials),
    },
)

# end_resource_dep_job

# start_resource_dep_job_runtime
credentials = Credentials.configure_at_launch()


@job
def connect():
    get_newest_stories()


defs = Definitions(
    jobs=[connect],
    resources={
        "credentials": credentials,
        "client": Client(credentials=credentials),
    },
)

# end_resource_dep_job_runtime

# start_resource_config
from dagster._config.structured_config import Resource


class DatabaseConnection(Resource):
    connection: str


# end_resource_config


def get_db_connection():
    return "foo"


def cleanup_db_connection(_db_conn):
    pass


# start_cm_resource
from contextlib import contextmanager


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


def do_something_with_resource(_):
    pass


class FooResource(Resource):
    pass


# start_asset_use_resource
from dagster import asset


@asset
def asset_requires_resource(foo: FooResource):
    do_something_with_resource(foo)


# end_asset_use_resource


@resource
def foo_resource():
    ...


# start_asset_provide_resource
from dagster import Definitions


defs = Definitions(
    assets=[asset_requires_resource],
    resources={"foo": foo_resource},
)

# end_asset_provide_resource


# start_asset_provide_resource_using_repository

from dagster import repository, with_resources


@repository
def repo():
    return [
        *with_resources(
            definitions=[asset_requires_resource],
            resource_defs={"foo": foo_resource},
        )
    ]


# end_asset_provide_resource_using_repository
