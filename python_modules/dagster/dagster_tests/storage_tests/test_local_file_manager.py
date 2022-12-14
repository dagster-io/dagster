import os
import tempfile
from contextlib import contextmanager

from dagster import LocalFileHandle, job, op
from dagster._core.instance import DagsterInstance
from dagster._core.storage.file_manager import LocalFileManager, local_file_manager
from dagster._core.test_utils import instance_for_test
from dagster._utils.temp_file import get_temp_file_handle_with_data


@contextmanager
def my_local_file_manager(instance, run_id):
    manager = None
    try:
        manager = LocalFileManager.for_instance(instance, run_id)
        yield manager
    finally:
        if manager:
            manager.delete_local_temp()


def test_basic_file_manager_copy_handle_to_local_temp():
    instance = DagsterInstance.ephemeral()
    foo_data = b"foo"
    with get_temp_file_handle_with_data(foo_data) as foo_handle:
        with my_local_file_manager(instance, "0") as manager:
            local_temp = manager.copy_handle_to_local_temp(foo_handle)
            assert local_temp != foo_handle.path
            with open(local_temp, "rb") as ff:
                assert ff.read() == foo_data


def test_basic_file_manager_execute():
    called = {}

    @op(required_resource_keys={"file_manager"})
    def file_handle(context):
        foo_bytes = b"foo"
        file_handle = context.resources.file_manager.write_data(foo_bytes)
        assert isinstance(file_handle, LocalFileHandle)
        with open(file_handle.path, "rb") as handle_obj:
            assert foo_bytes == handle_obj.read()

        with context.resources.file_manager.read(file_handle) as handle_obj:
            assert foo_bytes == handle_obj.read()

        file_handle = context.resources.file_manager.write_data(foo_bytes, ext="foo")
        assert isinstance(file_handle, LocalFileHandle)
        assert file_handle.path[-4:] == ".foo"

        with open(file_handle.path, "rb") as handle_obj:
            assert foo_bytes == handle_obj.read()

        with context.resources.file_manager.read(file_handle) as handle_obj:
            assert foo_bytes == handle_obj.read()

        called["yup"] = True

    @job(resource_defs={"file_manager": local_file_manager})
    def the_job():
        file_handle()

    with tempfile.TemporaryDirectory() as temp_dir:

        result = the_job.execute_in_process(
            run_config={"resources": {"file_manager": {"config": {"base_dir": temp_dir}}}},
        )
        assert result.success
        assert called["yup"]


def test_basic_file_manager_base_dir():
    called = {}

    @op(required_resource_keys={"file_manager"})
    def file_handle(context):
        assert context.resources.file_manager.base_dir == os.path.join(
            context.instance.storage_directory(), "file_manager"
        )
        called["yup"] = True

    @job(resource_defs={"file_manager": local_file_manager})
    def pipe():
        file_handle()

    with instance_for_test() as instance:
        result = pipe.execute_in_process(instance=instance)
        assert result.success
        assert called["yup"]
