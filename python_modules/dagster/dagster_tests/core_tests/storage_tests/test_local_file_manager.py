from dagster import LocalFileHandle, execute_solid, solid
from dagster.core.instance import DagsterInstance
from dagster.core.storage.file_manager import local_file_manager
from dagster.utils.temp_file import get_temp_file_handle_with_data


def test_basic_file_manager_copy_handle_to_local_temp():
    instance = DagsterInstance.ephemeral()
    foo_data = 'foo'.encode()
    with get_temp_file_handle_with_data(foo_data) as foo_handle:
        with local_file_manager(instance, '0') as manager:
            local_temp = manager.copy_handle_to_local_temp(foo_handle)
            assert local_temp != foo_handle.path
            with open(local_temp, 'rb') as ff:
                assert ff.read() == foo_data


def test_basic_file_manager_execute():
    called = {}

    @solid
    def file_handle(context):
        foo_bytes = 'foo'.encode()
        file_handle = context.file_manager.write_data(foo_bytes)
        assert isinstance(file_handle, LocalFileHandle)
        with open(file_handle.path, 'rb') as handle_obj:
            assert foo_bytes == handle_obj.read()

        with context.file_manager.read(file_handle) as handle_obj:
            assert foo_bytes == handle_obj.read()

        called['yup'] = True

    result = execute_solid(file_handle)
    assert result.success
    assert called['yup']
