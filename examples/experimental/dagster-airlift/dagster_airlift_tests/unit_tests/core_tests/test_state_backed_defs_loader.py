from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import record
from dagster._serdes.serdes import whitelist_for_serdes
from dagster_airlift.core.state_backed_defs_loader import (
    StateBackedDefinitionsLoader,
    scoped_reconstruction_serdes_objects,
)


def test_state_backed_defs_loader() -> None:
    @whitelist_for_serdes
    @record
    class ExampleDefState:
        a_string: str

    class ExampleStateBackedDefinitionsLoader(StateBackedDefinitionsLoader[ExampleDefState]):
        @property
        def defs_key(self) -> str:
            return "test_key"

        def fetch_state(self) -> ExampleDefState:
            return ExampleDefState(a_string="foo")

        def defs_from_state(self, state: ExampleDefState) -> Definitions:
            return Definitions([AssetSpec(key=state.a_string)])

    loader = ExampleStateBackedDefinitionsLoader()

    defs = loader.build_defs()

    assert len(defs.get_all_asset_specs()) == 1
    assert defs.get_assets_def("foo")

    with scoped_reconstruction_serdes_objects(dict(test_key=ExampleDefState(a_string="bar"))):
        loader_cached = ExampleStateBackedDefinitionsLoader()
        defs = loader_cached.build_defs()
        assert len(defs.get_all_asset_specs()) == 1
        assert defs.get_assets_def("bar")
