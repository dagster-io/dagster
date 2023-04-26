from typing import Any, Dict, Generator

import pytest
from dagster import (
    ConfigurableResource,
    job,
    op,
)
from dagster._core.errors import DagsterResourceFunctionError
from dagster._core.execution.context.init import InitResourceContext
from pydantic import PrivateAttr


def test_basic_pre_post_execute() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def pre_execute(self, context: InitResourceContext) -> None:
            log.append("pre_execute")

        def post_execute(self, context: InitResourceContext) -> None:
            log.append("post_execute")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        hello_world_op()

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "pre_execute",
        "hello_world_op",
        "post_execute",
    ]


def test_basic_yield() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("pre_execute")
            yield self
            log.append("post_execute")

    @op
    def hello_world_op(res: MyResource):
        log.append("hello_world_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        hello_world_op()

    result = hello_world_job.execute_in_process()
    assert result.success
    assert log == [
        "pre_execute",
        "hello_world_op",
        "post_execute",
    ]


def test_basic_pre_post_execute_multi_op() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def pre_execute(self, context: InitResourceContext) -> None:
            log.append("pre_execute")

        def post_execute(self, context: InitResourceContext) -> None:
            log.append("post_execute")

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
        "pre_execute",
        "hello_world_op",
        "another_hello_world_op",
        "post_execute",
    ]


def test_basic_yield_multi_op() -> None:
    log = []

    class MyResource(ConfigurableResource):
        def yield_for_execution(
            self, context: InitResourceContext
        ) -> Generator["MyResource", None, None]:
            log.append("pre_execute")
            yield self
            log.append("post_execute")

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
        "pre_execute",
        "hello_world_op",
        "another_hello_world_op",
        "post_execute",
    ]


def test_pre_post_execute_with_op_execution_error() -> None:
    # If an op raises an error, we should still call post_execute on the resource

    log = []

    class MyResource(ConfigurableResource):
        def pre_execute(self, context: InitResourceContext) -> None:
            log.append("pre_execute")

        def post_execute(self, context: InitResourceContext) -> None:
            log.append("post_execute")

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
        "pre_execute",
        "my_erroring_op",
        "post_execute",
    ]


def test_pre_execute_with_error() -> None:
    # If an error occurs in pre_execute, this error will manifest as a DagsterResourceFunctionError and
    # the resource teardown will be called

    log = []

    class MyResource(ConfigurableResource):
        def pre_execute(self, context: InitResourceContext) -> None:
            log.append("pre_execute")
            raise Exception("foo")

        def post_execute(self, context: InitResourceContext) -> None:
            log.append("post_execute")

    @op
    def my_never_run_op(res: MyResource):
        log.append("my_never_run_op")

    @job(resource_defs={"res": MyResource()})
    def hello_world_job() -> None:
        my_never_run_op()

    with pytest.raises(DagsterResourceFunctionError):
        hello_world_job.execute_in_process()

    assert log == [
        "pre_execute",
        "post_execute",
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

        def pre_execute(self, context: InitResourceContext) -> None:
            log.append(f"pre_execute with {self.username} and {self.password}")
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
        "pre_execute with foo and bar",
        "query select * from table with foo and bar",
    ]
