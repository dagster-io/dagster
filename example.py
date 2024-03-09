# from typing import Iterable
from dagster import Definitions, asset
from dagster._core.definitions.code_server import CodeLocation, CodeServer  # , ICodeServer


@asset
def an_asset_a() -> None:
    pass


class ACodeLocation(CodeLocation):
    name = "a_code_location"

    def load_definitions(self) -> Definitions:
        return Definitions([an_asset_a])


@asset
def an_asset_b() -> None:
    pass


class BCodeLocation(CodeLocation):
    name = "b_code_location"

    def load_definitions(self) -> Definitions:
        return Definitions([an_asset_b])


code_server = CodeServer(code_locations=[ACodeLocation(), BCodeLocation()])

# class CustomCodeServer(ICodeServer):
#     def load_code_locations(self) -> Iterable[CodeLocation]:
#         return [
#             ACodeLocationWithDefsBuiltFromPersistedState()
#         ]

# class ACodeLocationWithDefsBuiltFromPersistedState(CodeLocation):
#     name = "a_code_location"

#     def load_definitions(self) -> Definitions:
#         return Definitions(
#             build_assets_defs(
#                 get_serialized_representation_of_assets_from_storage()
#             )
#         )


# code_server = CustomCodeServer()
