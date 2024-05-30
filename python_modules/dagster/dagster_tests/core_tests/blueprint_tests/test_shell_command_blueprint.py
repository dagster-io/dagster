import re
import shutil
from typing import cast

from dagster import AssetKey, AssetsDefinition, MarkdownMetadataValue, materialize
from dagster._core.blueprints.blueprint import BlueprintDefinitions
from dagster._core.blueprints.blueprint_assets_definition import AssetSpecModel
from dagster._core.blueprints.shell_command_blueprint import ShellCommandBlueprint
from dagster._core.definitions.data_version import (
    DATA_VERSION_IS_USER_PROVIDED_TAG,
    DATA_VERSION_TAG,
)
from dagster._core.pipes.subprocess import PipesSubprocessClient
from dagster_tests.execution_tests.pipes_tests.test_subprocess import temp_script


def test_single_asset_shell_command_blueprint() -> None:
    single_asset_blueprint = ShellCommandBlueprint(
        assets=[AssetSpecModel(key="asset1")], command=["echo", '"hello"']
    )
    defs = single_asset_blueprint.build_defs()
    asset1 = cast(AssetsDefinition, next(iter(defs.assets)))
    assert asset1.key == AssetKey("asset1")
    assert materialize(
        [asset1], resources={"pipes_subprocess_client": PipesSubprocessClient()}
    ).success


def test_single_asset_shell_command_blueprint_pipes(capsys) -> None:
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.log.info("hello world")
            context.report_asset_materialization(
                metadata={"bar": {"raw_value": context.get_extra("bar"), "type": "md"}},
                data_version="alpha",
            )

    extras = {"bar": "baz"}
    with temp_script(script_fn) as script_path:
        single_asset_blueprint = ShellCommandBlueprint(
            assets=[AssetSpecModel(key="asset1")],
            command=[cast(str, shutil.which("python")), script_path],
            extras=extras,
        )
        defs = single_asset_blueprint.build_defs()
        asset1 = cast(AssetsDefinition, next(iter(defs.assets)))

        result = materialize(
            [asset1],
            resources={"pipes_subprocess_client": PipesSubprocessClient()},
        )

    mat = result.get_asset_materialization_events()[0].step_materialization_data.materialization
    assert isinstance(mat.metadata["bar"], MarkdownMetadataValue)
    assert mat.metadata["bar"].value == "baz"
    assert mat.tags
    assert mat.tags[DATA_VERSION_TAG] == "alpha"
    assert mat.tags[DATA_VERSION_IS_USER_PROVIDED_TAG]

    captured = capsys.readouterr()
    assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)


def test_multi_asset_shell_command_blueprint() -> None:
    multi_asset_blueprint = ShellCommandBlueprint(
        assets=[AssetSpecModel(key="asset1"), AssetSpecModel(key="asset2")],
        command=["echo", '"hello"'],
    )
    defs = multi_asset_blueprint.build_defs()
    assets = cast(AssetsDefinition, next(iter(defs.assets)))
    assert assets.keys == {AssetKey("asset1"), AssetKey("asset2")}
    assert materialize(
        [assets], resources={"pipes_subprocess_client": PipesSubprocessClient()}
    ).success


def test_multi_asset_shell_command_blueprint_pipes(capsys) -> None:
    def script_fn():
        from dagster_pipes import open_dagster_pipes

        with open_dagster_pipes() as context:
            context.log.info("hello world")
            context.report_asset_materialization(asset_key="asset1", metadata={"mkey": "mval"})
            context.report_asset_materialization(asset_key="asset2")

    with temp_script(script_fn) as script_path:
        multi_asset_blueprint = ShellCommandBlueprint(
            assets=[AssetSpecModel(key="asset1"), AssetSpecModel(key="asset2")],
            command=[cast(str, shutil.which("python")), script_path],
        )

        defs = multi_asset_blueprint.build_defs()
        assets = cast(AssetsDefinition, next(iter(defs.assets)))

        result = materialize(
            [assets],
            resources={"pipes_subprocess_client": PipesSubprocessClient()},
        )

    mat1 = result.get_asset_materialization_events()[0].step_materialization_data.materialization
    mat2 = result.get_asset_materialization_events()[1].step_materialization_data.materialization

    assert mat1.asset_key == AssetKey("asset1")
    assert mat1.metadata["mkey"].value == "mval"
    assert mat2.asset_key == AssetKey("asset2")

    captured = capsys.readouterr()
    assert re.search(r"dagster - INFO - [^\n]+ - hello world\n", captured.err, re.MULTILINE)


def test_op_name_collisions() -> None:
    single_asset_blueprint1 = ShellCommandBlueprint(
        assets=[AssetSpecModel(key="asset1")], command=["echo", '"hello"']
    )
    single_asset_blueprint2 = ShellCommandBlueprint(
        assets=[AssetSpecModel(key="asset2")], command=["echo", '"hello"']
    )
    resources = {"pipes_subprocess_client": PipesSubprocessClient()}
    blueprint_defs = BlueprintDefinitions.merge(
        single_asset_blueprint1.build_defs(),
        single_asset_blueprint2.build_defs(),
        BlueprintDefinitions(resources=resources),
    )
    blueprint_defs.to_definitions()

    materialize(
        [cast(AssetsDefinition, asset) for asset in blueprint_defs.assets], resources=resources
    )
