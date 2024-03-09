from abc import ABC, abstractmethod
from typing import Iterable, List

from dagster._core.definitions.definitions_class import Definitions


class ICodeServer(ABC):
    # User can override this method to perform any necessary setup when the code server starts
    def on_code_server_start(self) -> None: ...

    @abstractmethod
    def load_code_locations(self) -> Iterable["CodeLocation"]: ...


class CodeServer(ICodeServer):
    code_locations: List["CodeLocation"]

    def __init__(self, code_locations: List["CodeLocation"]):
        self.code_locations = code_locations

    def on_code_server_start(self) -> None: ...

    def load_code_locations(self) -> Iterable["CodeLocation"]:
        return self.code_locations


class CodeLocation(ABC):
    name: str

    @abstractmethod
    def load_definitions(self) -> Definitions: ...
