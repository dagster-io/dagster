from dagster import Definitions, asset
from dagster._core.definitions.code_server import CodeLocation, CodeServer


@asset
def an_asset() -> None:
    pass

class ACodeLocation(CodeLocation):
    name = "a_code_location"
    def load_definitions(self) -> Definitions:
        return Definitions([an_asset])


code_server = CodeServer(code_locations=[ACodeLocation()])