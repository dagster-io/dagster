import contextlib
import re
from typing import Any, Dict, Generator

import pytest
from dagster import (
    ConfigurableResource,
    Definitions,
    EnvVar,
    RunConfig,
    build_init_resource_context,
    job,
    op,
)
from dagster._check import CheckError
from dagster._core.errors import DagsterResourceFunctionError
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.test_utils import environ
from pydantic import PrivateAttr


def test_basic_pre_teardown_after_execution() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")

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
        "teardown_after_execution",
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
            log.append("teardown_after_execution")

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
        "teardown_after_execution",
    ]


def test_basic_pre_teardown_after_execution_multi_op() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")

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
        "teardown_after_execution",
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
            log.append("teardown_after_execution")

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
        "teardown_after_execution",
    ]


def test_pre_teardown_after_execution_with_op_execution_error() -> None:
    # If an op raises an error, we should still call teardown_after_execution on the resource

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")

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
        "teardown_after_execution",
    ]


def test_setup_for_execution_with_error() -> None:
    # If an error occurs in setup_for_execution, this error will manifest as a DagsterResourceFunctionError
    # The resource teardown will not be called

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")
            raise Exception("my setup function errored!")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")

    @op
    def my_never_run_op(res: MyResource):
        log.append("my_never_run_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_never_run_op()

    with pytest.raises(
        DagsterResourceFunctionError, match="Error executing resource_fn on ResourceDefinition res"
    ):
        hello_world_job.execute_in_process()

    # The op should not run and the teardown should not be called
    assert log == [
        "setup_for_execution",
    ]


def test_teardown_after_execution_with_error() -> None:
    # If an error occurs in teardown_after_execution, this error will manifest as a DagsterResourceFunctionError

    log = []

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")
            raise Exception("my teardown function errored!")

    @op
    def my_hello_world_op(res: MyResource):
        log.append("my_hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_hello_world_op()

    result = hello_world_job.execute_in_process()

    # Ensure we record that the teardown errored in the event log
    # this doesnt cause the run to fail
    assert any(
        re.search(r"Teardown of resources \[.*\] failed", event.message or "")
        for event in result.all_events
    )

    assert log == [
        "setup_for_execution",
        "my_hello_world_op",
        "teardown_after_execution",
    ]


def test_yield_for_execution_with_error_before_yield() -> None:
    # If an error occurs in yield_for_execution, the error will manifest as a DagsterResourceFunctionError
    # if it occurs before the resource is yielded, or as a cleanup error in the log if it occurs after the resource
    # is yielded

    log = []

    class MyResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("yield_for_execution_start")
            raise Exception("my yield function errored!")

    @op
    def my_never_run_op(res: MyResource):
        log.append("my_never_run_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_never_run_op()

    with pytest.raises(
        DagsterResourceFunctionError, match="Error executing resource_fn on ResourceDefinition res"
    ):
        hello_world_job.execute_in_process()

    # The op should not run and the teardown should not be called
    assert log == [
        "yield_for_execution_start",
    ]


def test_yield_for_execution_with_error_after_yield() -> None:
    # If an error occurs after the yield, this will not fail the run but will be recorded in the event log

    log = []

    class MyResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("yield_for_execution_start")
            yield self
            log.append("yield_for_execution_post_yield")
            raise Exception("my yield function errored!")

    @op
    def my_hello_world_op(res: MyResource):
        log.append("my_hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_hello_world_op()

    result = hello_world_job.execute_in_process()

    # Ensure we record that the teardown errored in the event log
    # this doesnt cause the run to fail
    assert any(
        re.search(r"Teardown of resources \[.*\] failed", event.message or "")
        for event in result.all_events
    )

    assert log == [
        "yield_for_execution_start",
        "my_hello_world_op",
        "yield_for_execution_post_yield",
    ]


def test_setup_for_execution_with_error_multi_resource() -> None:
    log = []

    resources_initialized = [0]

    class MyResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution")
            resources_initialized[0] += 1
            if resources_initialized[0] == 2:
                log.append("raising error")
                raise Exception("my setup function errored!")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution")

    class MySecondResource(ConfigurableResource):
        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append("setup_for_execution_second")
            resources_initialized[0] += 1
            if resources_initialized[0] == 2:
                log.append("raising error")
                raise Exception("my setup function errored!")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            log.append("teardown_after_execution_second")

    @op
    def my_never_run_op(first: MyResource, second: MySecondResource):
        log.append("my_never_run_op")

    @job(resource_defs={"first": MyResource(), "second": MySecondResource()})
    def hello_world_job() -> None:
        my_never_run_op()

    with pytest.raises(
        DagsterResourceFunctionError,
        match="Error executing resource_fn on ResourceDefinition second",
    ):
        hello_world_job.execute_in_process()

    # order is not deterministic
    assert log == [
        "setup_for_execution",
        "setup_for_execution_second",
        "raising error",
        "teardown_after_execution",
    ] or log == [
        "setup_for_execution_second",
        "setup_for_execution",
        "raising error",
        "teardown_after_execution_second",
    ]


def test_multiple_yield_ordering() -> None:
    # ensure proper ordering of yield_for_execution

    log = []

    class MyResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("yield_start_my_resource")
            yield self
            log.append("yield_end_my_resource")

    class MySecondResource(ConfigurableResource):
        @contextlib.contextmanager
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MySecondResource", None, None]:
            log.append("yield_start_second_resource")
            yield self
            log.append("yield_end_second_resource")

    @op
    def my_hello_world_op(first: MyResource, second: MySecondResource):
        log.append("my_hello_world_op")

    @job
    def hello_world_job() -> None:
        my_hello_world_op()

    defs = Definitions(
        jobs=[hello_world_job], resources={"first": MyResource(), "second": MySecondResource()}
    )

    assert defs.get_job_def("hello_world_job").execute_in_process().success

    # order is not deterministic
    assert log == [
        "yield_start_my_resource",
        "yield_start_second_resource",
        "my_hello_world_op",
        "yield_end_second_resource",
        "yield_end_my_resource",
    ] or log == [
        "yield_start_second_resource",
        "yield_start_my_resource",
        "my_hello_world_op",
        "yield_end_my_resource",
        "yield_end_second_resource",
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


def test_direct_invocation_from_context() -> None:
    log = []

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = "my_jwt"
            log.append("setup_for_execution")

        @property
        def jwt(self) -> str:
            return self._jwt

    res = AWSCredentialsResource.from_resource_context(
        build_init_resource_context(config={"access_key": "my_key", "secret_key": "my_secret"})
    )
    assert res.jwt == "my_jwt"
    assert log == ["setup_for_execution"]

    # no need to use a context manager, but still works
    log.clear()
    with AWSCredentialsResource.from_resource_context_cm(
        build_init_resource_context(config={"access_key": "my_key", "secret_key": "my_secret"})
    ) as res:
        assert res.jwt == "my_jwt"
        assert log == ["setup_for_execution"]


def test_direct_invocation_from_context_cm() -> None:
    log = []

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = "my_jwt"
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            del self._jwt
            log.append("teardown_after_execution")

        @property
        def jwt(self) -> str:
            return self._jwt

    # need to use a context manager to ensure teardown is called
    with pytest.raises(CheckError):
        AWSCredentialsResource.from_resource_context(
            build_init_resource_context(config={"access_key": "my_key", "secret_key": "my_secret"})
        )

    log.clear()
    with AWSCredentialsResource.from_resource_context_cm(
        build_init_resource_context(config={"access_key": "my_key", "secret_key": "my_secret"})
    ) as res:
        assert res.jwt == "my_jwt"
        assert log == ["setup_for_execution"]
    assert log == ["setup_for_execution", "teardown_after_execution"]


def test_process_config_and_initialize_cm() -> None:
    log = []

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = "my_jwt"
            log.append("setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            del self._jwt
            log.append("teardown_after_execution")

        @property
        def jwt(self) -> str:
            return self._jwt

    log.clear()
    with environ({"ENV_ACCESS_KEY": "my_key"}):
        with AWSCredentialsResource(
            access_key=EnvVar("ENV_ACCESS_KEY"), secret_key="my_secret"
        ).process_config_and_initialize_cm() as res:
            assert res.access_key == "my_key"
            assert res.jwt == "my_jwt"
            assert log == ["setup_for_execution"]

    assert log == ["setup_for_execution", "teardown_after_execution"]


def test_process_config_and_initialize_cm_nested() -> None:
    log = []

    class AWSCredentialsResource(ConfigurableResource):
        access_key: str
        secret_key: str

        _jwt: str = PrivateAttr()

        def setup_for_execution(self, context: InitResourceContext) -> None:
            self._jwt = "my_jwt"
            log.append("inner_setup_for_execution")

        def teardown_after_execution(self, context: InitResourceContext) -> None:
            del self._jwt
            log.append("inner_teardown_after_execution")

        @property
        def jwt(self) -> str:
            return self._jwt

    class S3Resource(ConfigurableResource):
        credentials: AWSCredentialsResource
        label: str

        def setup_for_execution(self, context: InitResourceContext) -> None:
            log.append(f"setup_for_execution with jwt {self.credentials.jwt}")

    log.clear()
    with environ({"ENV_ACCESS_KEY": "my_key", "ENV_LABEL": "foo"}):
        with S3Resource(
            label=EnvVar("ENV_LABEL"),
            credentials=AWSCredentialsResource(
                access_key=EnvVar("ENV_ACCESS_KEY"), secret_key="my_secret"
            ),
        ).process_config_and_initialize_cm() as res:
            assert res.label == "foo"
            creds = res.credentials
            assert creds.access_key == "my_key"
            assert creds.jwt == "my_jwt"
            assert log == ["inner_setup_for_execution", "setup_for_execution with jwt my_jwt"]

    assert log == [
        "inner_setup_for_execution",
        "setup_for_execution with jwt my_jwt",
        "inner_teardown_after_execution",
    ]
