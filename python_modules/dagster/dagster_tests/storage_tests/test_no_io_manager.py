from typing import Any

from dagster import (
    IOManager,
    asset,
    job,
    materialize,
    op,
)


class TestIOManager(IOManager):
    def __init__(self, return_value: Any = None):
        self.handled_output = False
        self.loaded_input = False
        self.return_value = return_value

    def handle_output(self, context, obj) -> None:
        self.handled_output = True

    def load_input(self, context):
        self.loaded_input = True

        return self.return_value


def test_return_none_no_type_annotation():
    @asset
    def returns_none():
        return None

    io_mgr = TestIOManager()

    materialize([returns_none], resources={"io_manager": io_mgr})

    assert io_mgr.handled_output
    assert not io_mgr.loaded_input


def test_return_none_with_type_annotation():
    @asset
    def returns_none() -> None:
        return None

    io_mgr = TestIOManager()

    materialize([returns_none], resources={"io_manager": io_mgr})

    assert not io_mgr.handled_output
    assert not io_mgr.loaded_input


def test_downstream_deps_with_type_annotation():
    @asset
    def returns_none() -> None:
        return None

    @asset(deps=[returns_none])
    def downstream() -> None:
        return None

    io_mgr = TestIOManager()

    materialize([returns_none, downstream], resources={"io_manager": io_mgr})

    assert not io_mgr.handled_output
    assert not io_mgr.loaded_input


def test_downstream_managed_deps():
    @asset
    def returns_none():
        return None

    @asset
    def downstream(returns_none):
        assert returns_none == 1

    io_mgr = TestIOManager(return_value=1)

    materialize([returns_none, downstream], resources={"io_manager": io_mgr})

    assert io_mgr.handled_output
    assert io_mgr.loaded_input


def test_downstream_managed_deps_with_type_annotation():
    # Tests that the return type None annotation does not use the I/O manager, but you can still
    # use an I/O manager to load it as a downstream input if the I/O manager is set up to handle that
    # case, i.e. a third party writes data to the place the I/O manager expects it to exist
    @asset
    def returns_none() -> None:
        return None

    @asset
    def downstream(returns_none) -> None:
        assert returns_none == 1

    io_mgr = TestIOManager(return_value=1)

    materialize([returns_none, downstream], resources={"io_manager": io_mgr})

    assert not io_mgr.handled_output
    assert io_mgr.loaded_input


def test_ops_no_type_annotation():
    @op
    def returns_none():
        return None

    @op
    def asserts_none(x):
        assert x == 1

    @job
    def return_none_job():
        asserts_none(returns_none())

    io_mgr = TestIOManager(return_value=1)

    result = return_none_job.execute_in_process(resources={"io_manager": io_mgr})
    assert result.success
    assert io_mgr.handled_output
    assert io_mgr.loaded_input


def test_ops_with_type_annotation():
    # Tests that the return type None annotation does not use the I/O manager, but you can still
    # use an I/O manager to load it as a downstream input if the I/O manager is set up to handle that
    # case, i.e. a third party writes data to the place the I/O manager expects it to exist
    @op
    def returns_none() -> None:
        return None

    @op
    def asserts_none(x) -> None:
        assert x == 1

    @job
    def return_none_job():
        asserts_none(returns_none())

    io_mgr = TestIOManager(return_value=1)

    result = return_none_job.execute_in_process(resources={"io_manager": io_mgr})
    assert result.success
    assert not io_mgr.handled_output
    assert io_mgr.loaded_input
