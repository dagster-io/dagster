from dagster import IOManager, InputContext, OutputContext


class MyIOManager(IOManager):
    def __init__(self):
        self.storage_dict = {}

    def handle_output(self, context, obj):
        self.storage_dict[(context.step_key, context.name)] = obj

    def load_input(self, context):
        return self.storage_dict[(context.upstream_output.step_key, context.upstream_output.name)]


def test_my_io_manager_handle_output():
    my_io_manager = MyIOManager()
    context = OutputContext(name="abc", step_key="123")
    my_io_manager.handle_output(context, 5)
    assert my_io_manager.storage_dict[("123", "abc")] == 5


def test_my_io_manager_load_input():
    my_io_manager = MyIOManager()
    my_io_manager.storage_dict[("123", "abc")] = 5

    context = InputContext(upstream_output=OutputContext(name="abc", step_key="123"))
    assert my_io_manager.load_input(context) == 5
