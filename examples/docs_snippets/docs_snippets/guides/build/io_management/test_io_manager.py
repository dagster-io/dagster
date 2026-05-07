import dagster as dg


class MyIOManager(dg.IOManager):
    def __init__(self):
        self.storage_dict = {}

    def handle_output(self, context: dg.OutputContext, obj):
        self.storage_dict[(context.step_key, context.name)] = obj

    def load_input(self, context: dg.InputContext):
        if context.upstream_output:
            return self.storage_dict[
                (context.upstream_output.step_key, context.upstream_output.name)
            ]


def test_my_io_manager_handle_output():
    manager = MyIOManager()
    context = dg.build_output_context(name="abc", step_key="123")
    manager.handle_output(context, 5)
    assert manager.storage_dict[("123", "abc")] == 5


def test_my_io_manager_load_input():
    manager = MyIOManager()
    manager.storage_dict[("123", "abc")] = 5

    context = dg.build_input_context(
        upstream_output=dg.build_output_context(name="abc", step_key="123")
    )
    assert manager.load_input(context) == 5
