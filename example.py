# from typing import Iterable
from typing import Mapping

from dagster import Definitions, asset
from dagster._core.definitions.code_server import CodeLocation, MultiDefinitionsCodeLocation


@asset
def an_asset_a() -> None:
    pass


class ACodeLocation(CodeLocation):
    # could put metadata here
    # team = "some team name"
    def load_definitions(self) -> Definitions:
        return Definitions([an_asset_a])


code_location = ACodeLocation()


@asset
def an_asset_b() -> None:
    pass


class ABCodeLocation(MultiDefinitionsCodeLocation):
    def load_definitions_dict(self) -> Mapping[str, Definitions]:
        return {"a_defs": Definitions([an_asset_a]), "b_defs": Definitions([an_asset_b])}


code_location = ABCodeLocation()

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
