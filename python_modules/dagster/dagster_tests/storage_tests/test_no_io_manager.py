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
        assert returns_none is None

    io_mgr = TestIOManager()

    materialize([returns_none, downstream], resources={"io_manager": io_mgr})

    assert io_mgr.handled_output
    assert io_mgr.loaded_input


def test_downstream_managed_deps_with_type_annotation():
    # this tests a kind of funny case where the return type annotation is -> None for the first
    # asset, thus bypassing the I/O manager, but a downstream asset wants to load the value for the
    # first asset. In practice, this would likely cause an error because the I/O manager will be looking for
    # a storage location that was never created. In this test we just manually set what we want the
    # I/O manager to return and then confirm that it happens as expected

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


def test_ops():
    @op
    def returns_none():
        return None

    @op
    def asserts_none(x):
        assert x is None

    @job
    def return_none_job():
        asserts_none(returns_none())

    io_mgr = TestIOManager()

    result = return_none_job.execute_in_process(resources={"io_manager": io_mgr})
    assert result.success
    assert io_mgr.handled_output
    assert io_mgr.loaded_input
