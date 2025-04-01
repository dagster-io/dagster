from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize

from dagster_components_tests.integration_tests.component_loader import (
    chdir as chdir,
    load_test_component_defs,
)


def test_step_one() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_one") as defs:
        assert isinstance(defs, Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.get_all_asset_specs()}

        assert "the_key" in specs

        assets_def = defs.get_assets_def("the_key")

        assert materialize([assets_def]).success


def test_step_two() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_two") as defs:
        assert isinstance(defs, Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.get_all_asset_specs()}

        assert "step_two_key" in specs

        assets_def = defs.get_assets_def("step_two_key")
        assert assets_def.op.name == "run_step_two_key"
        assert materialize([assets_def]).success


def test_step_three() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_three") as defs:
        assert isinstance(defs, Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.get_all_asset_specs()}

        assert "step_three_key_1" in specs

        assets_def = defs.get_assets_def("step_three_key_1")
        assert materialize([assets_def]).success


def test_step_four() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_four") as defs:
        assert isinstance(defs, Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.get_all_asset_specs()}

        assert "step_four_key_1" in specs

        assets_def = defs.get_assets_def("step_four_key_1")
        assert materialize([assets_def]).success
