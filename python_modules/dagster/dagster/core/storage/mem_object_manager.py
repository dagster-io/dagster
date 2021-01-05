from dagster.core.storage.object_manager import ObjectManager, object_manager


class InMemoryObjectManager(ObjectManager):
    def __init__(self):
        self.values = {}

    def handle_output(self, context, obj):
        keys = tuple(context.get_run_scoped_output_identifier())
        self.values[keys] = obj

    def load_input(self, context):
        keys = tuple(context.get_run_scoped_output_identifier())
        return self.values[keys]


@object_manager
def mem_object_manager(_):
    """Built-in object manager that stores and retrieves values in memory."""

    return InMemoryObjectManager()
