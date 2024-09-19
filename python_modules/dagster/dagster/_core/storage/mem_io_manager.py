from typing import Dict, Tuple

from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, dagster_maintained_io_manager, io_manager


class InMemoryIOManager(IOManager):
    """I/O manager that stores and retrieves values in memory. After execution is complete, the values will
    be garbage-collected. Note that this means that each run will not have access to values from previous runs.
    """

    def __init__(self):
        self.values: Dict[Tuple[object, ...], object] = {}

    def handle_output(self, context: OutputContext, obj: object):
        keys = tuple(context.get_identifier())
        self.values[keys] = obj

    def load_input(self, context: InputContext) -> object:
        keys = tuple(context.get_identifier())
        return self.values[keys]


@dagster_maintained_io_manager
@io_manager(description="Built-in IO manager that stores and retrieves values in memory.")
def mem_io_manager(_) -> InMemoryIOManager:
    """Built-in IO manager that stores and retrieves values in memory."""
    return InMemoryIOManager()
