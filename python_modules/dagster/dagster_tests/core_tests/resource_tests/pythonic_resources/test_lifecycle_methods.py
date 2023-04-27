import contextlib
from typing import Any, Dict, Generator

import pytest
from dagster import (
    ConfigurableResource,
    Definitions,
    RunConfig,
    job,
    op,
)
from dagster._core.errors import DagsterResourceFunctionError
from dagster._core.execution.context.init import InitResourceContext
from pydantic import PrivateAttr


def test_basic_pre_teardown_for_execution() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_for_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_for_execution")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        hello_world_op()

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "setup_for_execution",
        "hello_world_op",
        "teardown_for_execution",
    ]


def test_basic_yield() -> None:
    log = []

    class MyResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("setup_for_execution")
            yield self
            log.append("teardown_for_execution")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        hello_world_op()

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "setup_for_execution",
        "hello_world_op",
        "teardown_for_execution",
    ]


def test_basic_pre_teardown_for_execution_multi_op() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_for_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_for_execution")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @op
    def another_hello_world_op(res: MyResource, _: Any):
        log.append("another_hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        another_hello_world_op(hello_world_op())

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "setup_for_execution",
        "hello_world_op",
        "another_hello_world_op",
        "teardown_for_execution",
    ]


def test_basic_yield_multi_op() -> None:
    log = []

    class MyResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("setup_for_execution")
            yield self
            log.append("teardown_for_execution")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @op
    def another_hello_world_op(res: MyResource, _: Any):
        log.append("another_hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        another_hello_world_op(hello_world_op())

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "setup_for_execution",
        "hello_world_op",
        "another_hello_world_op",
        "teardown_for_execution",
    ]


def test_pre_teardown_for_execution_with_op_execution_error() -> None:
    # If an op raises an error, we should still call teardown_for_execution on the resource

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_for_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_for_execution")

    @op
    def my_erroring_op(res: MyResource):
        log.append("my_erroring_op")
        raise Exception("foo")

    @op
    def my_never_run_op(res: MyResource, _: Any):
        log.append("my_never_run_op")

    @job(resource_defs={"res": MyResource()})
    def erroring_job() -> None:
        my_never_run_op(my_erroring_op())

    with pytest.raises(Exception, match="foo"):
        erroring_job.execute_in_process()

    assert log == [
        "setup_for_execution",
        "my_erroring_op",
        "teardown_for_execution",
    ]


def test_setup_for_execution_with_error() -> None:
    # If an error occurs in setup_for_execution, this error will manifest as a DagsterResourceFunctionError and
    # the resource teardown will be called

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")
            raise Exception("foo")

        def teardown_for_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_for_execution")

    @op
    def my_never_run_op(res: MyResource):
        log.append("my_never_run_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_never_run_op()

    with pytest.raises(DagsterResourceFunctionError):
        hello_world_job.execute_in_process()

    assert log == [
        "setup_for_execution",
        "teardown_for_execution",
    ]


def test_teardown_for_execution_with_error() -> None:
    # If an error occurs in teardown_for_execution, this error will manifest as a DagsterResourceFunctionError

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_for_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_for_execution")
            raise Exception("foo")

    @op
    def my_hello_world_op(res: MyResource):
        log.append("my_hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_hello_world_op()

    hello_world_job.execute_in_process()

    assert log == [
        "setup_for_execution",
        "my_hello_world_op",
        "teardown_for_execution",
    ]


def test_basic_init_with_privateattr() -> None:
    log = []

    class Connection:
        def __init__(self, username: str, password: str):
            self.username = username
            self.password = password

    class MyDBResource(ConfigurableResource):
        username: str
        password: str

        _connection: Connection = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append(f"setup_for_execution with {self.username} and {self.password}")
            self._connection = Connection(self.username, self.password)

        def query(self, query: str) -> Dict[str, Any]:
            log.append(
                f"query {query} with {self._connection.username} and {self._connection.password}"
            )
            return {"foo": "bar"}

    @op
    def hello_world_op(db: MyDBResource):
        res = db.query("select * from table")
        assert res == {"foo": "bar"}

    @job(resource_defs={"db": MyDBResource(username="foo", password="bar")})
    def hello_world_job() -> None:
        hello_world_op()

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "setup_for_execution with foo and bar",
        "query select * from table with foo and bar",
    ]


def test_nested_resources_init_with_privateattr() -> None:
    log = []

    def fetch_jwt(access_key: str, secret_key: str) -> str:
        log.append(f"fetch_jwt with {access_key} and {secret_key}")
        return "my_jwt"

    class S3Client:
        def __init__(self, jwt: str):
            self.jwt = jwt

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = fetch_jwt(self.access_key, self.secret_key)

        @property
        def jwt(self) -> str:
            return self._jwt

    class S3Resource(ConfigurableResource):
        credentials: AWSCredentialsResource

        _s3_client: Any = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append(f"setup_for_execution with jwt {self.credentials.jwt}")
            self._s3_client = S3Client(self.credentials.jwt)

        def get_object(self, bucket: str, key: str) -> Dict[str, Any]:
            log.append(f"get_object {bucket} {key} with jwt {self.credentials.jwt}")
            return {"foo": "bar"}

    @op
    def load_from_s3_op(s3: S3Resource) -> Dict[str, Any]:
        log.append("load_from_s3_op")
        res = s3.get_object("my-bucket", "my-key")
        assert res == {"foo": "bar"}
        return res

    @job(
        resource_defs={
            "s3": S3Resource(
                credentials=AWSCredentialsResource(access_key="my_key", secret_key="my_secret")
            )
        }
    )
    def load_from_s3_job() -> None:
        load_from_s3_op()

    result = load_from_s3_job.execute_in_process()
    assert result.success
    assert log == [
        "fetch_jwt with my_key and my_secret",
        "setup_for_execution with jwt my_jwt",
        "load_from_s3_op",
        "get_object my-bucket my-key with jwt my_jwt",
    ]


def test_nested_resources_init_with_privateattr_runtime_config() -> None:
    log = []

    def fetch_jwt(access_key: str, secret_key: str) -> str:
        log.append(f"fetch_jwt with {access_key} and {secret_key}")
        return "my_jwt"

    class S3Client:
        def __init__(self, jwt: str):
            self.jwt = jwt

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = fetch_jwt(self.access_key, self.secret_key)

        @property
        def jwt(self) -> str:
            return self._jwt

    class S3Resource(ConfigurableResource):
        credentials: AWSCredentialsResource

        _s3_client: Any = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append(f"setup_for_execution with jwt {self.credentials.jwt}")
            self._s3_client = S3Client(self.credentials.jwt)

        def get_object(self, bucket: str, key: str) -> Dict[str, Any]:
            log.append(f"get_object {bucket} {key} with jwt {self.credentials.jwt}")
            return {"foo": "bar"}

    @op
    def load_from_s3_op(s3: S3Resource) -> Dict[str, Any]:
        log.append("load_from_s3_op")
        res = s3.get_object("my-bucket", "my-key")
        assert res == {"foo": "bar"}
        return res

    credentials = AWSCredentialsResource.configure_at_launch()

    @job
    def load_from_s3_job() -> None:
        load_from_s3_op()

    defs = Definitions(
        jobs=[load_from_s3_job],
        resources={"credentials": credentials, "s3": S3Resource(credentials=credentials)},
    )

    result = defs.get_job_def("load_from_s3_job").execute_in_process(
        run_config=RunConfig(
            resources={
                "credentials": AWSCredentialsResource(access_key="my_key", secret_key="my_secret")
            }
        )
    )
    assert result.success
    assert log == [
        "fetch_jwt with my_key and my_secret",
        "setup_for_execution with jwt my_jwt",
        "load_from_s3_op",
        "get_object my-bucket my-key with jwt my_jwt",
    ]
