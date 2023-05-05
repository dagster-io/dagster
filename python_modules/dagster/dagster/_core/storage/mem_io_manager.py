from typing import Dict, Tuple

from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, io_manager


class InMemoryIOManager(IOManager):
    def __init__(self):
        self.values: Dict[Tuple[object, ...], object] = {}

    def handle_output(self, context: OutputContext, obj: object):
        keys = tuple(context.get_identifier())
        self.values[keys] = obj

    def load_input(self, context: InputContext) -> object:
        keys = tuple(context.get_identifier())
        return self.values[keys]


@io_manager(description="Built-in IO manager that stores and retrieves values in memory.")
def mem_io_manager(_) -> InMemoryIOManager:
    """Built-in IO manager that stores and retrieves values in memory."""
    return InMemoryIOManager()
