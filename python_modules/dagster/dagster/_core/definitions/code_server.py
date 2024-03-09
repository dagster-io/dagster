from abc import ABC, abstractmethod
from typing import List

from dagster._core.definitions.definitions_class import Definitions


class CodeServer:
    code_locations: List["CodeLocation"]

    def __init__(self, code_locations: List["CodeLocation"]):
        self.code_locations = code_locations

    def on_code_server_start(self) -> None:
        ...

class CodeLocation(ABC):
    name: str

    @abstractmethod
    def load_definitions(self) -> Definitions: ...
