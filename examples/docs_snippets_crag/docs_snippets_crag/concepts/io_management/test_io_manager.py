from dagster import IOManager, build_input_context, build_output_context, io_manager


class MyIOManager(IOManager):
    def __init__(self):
        self.storage_dict = {}

    def handle_output(self, context, obj):
        self.storage_dict[(context.step_key, context.name)] = obj

    def load_input(self, context):
        return self.storage_dict[(context.upstream_output.step_key, context.upstream_output.name)]


@io_manager
def my_io_manager(_):
    return MyIOManager()


def test_my_io_manager_handle_output():
    manager = my_io_manager(None)
    context = build_output_context(name="abc", step_key="123")
    manager.handle_output(context, 5)
    assert manager.storage_dict[("123", "abc")] == 5


def test_my_io_manager_load_input():
    manager = my_io_manager(None)
    manager.storage_dict[("123", "abc")] = 5

    context = build_input_context(upstream_output=build_output_context(name="abc", step_key="123"))
    assert manager.load_input(context) == 5
