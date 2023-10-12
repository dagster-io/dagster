from dagster import (
    IOManager,
    build_input_context,
    build_output_context,
    OutputContext,
    InputContext
)


class MyIOManager(IOManager):
    def __init__(self):
        self.storage_dict = {}

    def handle_output(self, context: OutputContext, obj):
        self.storage_dict[(context.step_key, context.name)] = obj

    def load_input(self, context: InputContext):
        return self.storage_dict[
            (context.upstream_output.step_key, context.upstream_output.name)
        ]


def test_my_io_manager_handle_output():
    manager = MyIOManager()
    context = build_output_context(name="abc", step_key="123")
    manager.handle_output(context, 5)
    assert manager.storage_dict[("123", "abc")] == 5


def test_my_io_manager_load_input():
    manager = MyIOManager()
    manager.storage_dict[("123", "abc")] = 5

    context = build_input_context(
        upstream_output=build_output_context(name="abc", step_key="123")
    )
    assert manager.load_input(context) == 5
