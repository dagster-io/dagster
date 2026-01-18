import dagster as dg
from dagster_shared import check

from dagster_tests.components_tests.integration_tests.component_loader import (
    chdir as chdir,
    load_test_component_defs,
)


def test_step_one() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_one") as defs:
        assert isinstance(defs, dg.Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.resolve_all_asset_specs()}

        assert "the_key" in specs

        assets_def = defs.resolve_assets_def("the_key")
        refs = check.inst(
            assets_def.metadata_by_key[dg.AssetKey("the_key")]["dagster/code_references"],
            dg.CodeReferencesMetadataValue,
        )

        assert len(refs.code_references) == 1
        assert isinstance(refs.code_references[0], dg.LocalFileCodeReference)
        assert refs.code_references[0].file_path.endswith("defs/step_one/defs.yaml")

        assert dg.materialize([assets_def]).success


def test_step_two() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_two") as defs:
        assert isinstance(defs, dg.Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.resolve_all_asset_specs()}

        assert "step_two_key" in specs

        assets_def = defs.resolve_assets_def("step_two_key")
        assert assets_def.op.name == "run_step_two_key"
        assert dg.materialize([assets_def]).success


def test_step_three() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_three") as defs:
        assert isinstance(defs, dg.Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.resolve_all_asset_specs()}

        assert "step_three_key_1" in specs

        assets_def = defs.resolve_assets_def("step_three_key_1")
        assert dg.materialize([assets_def]).success


def test_step_four() -> None:
    with load_test_component_defs("iwritesqlbutnotdbt/step_four") as defs:
        assert isinstance(defs, dg.Definitions)

        specs = {ak.key.to_user_string(): ak for ak in defs.resolve_all_asset_specs()}

        assert "step_four_key_1" in specs

        assets_def = defs.resolve_assets_def("step_four_key_1")
        assert dg.materialize([assets_def]).success
