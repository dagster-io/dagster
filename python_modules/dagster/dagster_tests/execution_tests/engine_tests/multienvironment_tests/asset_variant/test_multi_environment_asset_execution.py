import tempfile
from typing import NamedTuple, Sequence

from dagster import Definitions
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.input import In
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.execution.api import execute_job
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.multi_environment.multi_environment_step_handler import (
    MultiEnvironmentExecutor,
    RemoteEnvironmentSingleStepHandler,
)
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path

from dagster_tests.execution_tests.engine_tests.multienvironment_tests.python_script_single_step_handler import (
    PythonScriptSingleStepHandler,
)


class RemoteAsset(NamedTuple):
    asset_key: CoercibleToAssetKey
    upstream_asset_keys: Sequence[CoercibleToAssetKey]
    single_step_handler: RemoteEnvironmentSingleStepHandler


def remote_asset_in_script(asset_key: str, upstream_asset_keys: Sequence[str]):
    return RemoteAsset(
        asset_key=asset_key,
        upstream_asset_keys=upstream_asset_keys,
        # you can customize step handling per step
        single_step_handler=PythonScriptSingleStepHandler(
            file_relative_path(__file__, f"{asset_key}.py")
        ),
    )


def build_definitions_for_remote_assets(
    asset_job_name: str, remote_assets: Sequence[RemoteAsset]
) -> Definitions:
    def _never_called(*args, **kwargs):
        raise Exception("This assets exists only for metadata. Should not be called.")

    assets_defs = []

    for remote_asset in remote_assets:
        asset_key = AssetKey.from_coerceable(remote_asset.asset_key)
        upstream_asset_keys = [
            AssetKey.from_coerceable(uak) for uak in remote_asset.upstream_asset_keys
        ]
        keys_by_input_name = {
            upstream_asset_key.to_python_identifier(): upstream_asset_key
            for upstream_asset_key in upstream_asset_keys
        }
        keys_by_output_name = {"result": asset_key}
        op_def = OpDefinition(
            compute_fn=_never_called,
            name=asset_key.to_user_string(),
            ins={
                upstream_asset_key.to_python_identifier(): In()
                for upstream_asset_key in upstream_asset_keys
            },
        )
        assets_defs.append(
            AssetsDefinition(
                keys_by_input_name=keys_by_input_name,
                keys_by_output_name=keys_by_output_name,
                node_def=op_def,
            )
        )

    assets_to_handlers = {
        remote_asset.asset_key: remote_asset.single_step_handler for remote_asset in remote_assets
    }

    return Definitions(
        assets=assets_defs,
        jobs=[define_asset_job(asset_job_name, "*")],
        executor=MultiEnvironmentExecutor(
            lambda step_context: assets_to_handlers[step_context.step.key],
            retries=RetryMode.DISABLED,
            check_step_health_interval_seconds=1,
        ),
    )


def get_defs_for_one_asset():
    return build_definitions_for_remote_assets(
        "one_asset_job", [remote_asset_in_script("one_asset", [])]
    )


def get_one_asset_job():
    return get_defs_for_one_asset().get_job_def("one_asset_job")


def test_one_asset_on_its_own():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test(temp_dir=tmpdir_path) as instance:
            with execute_job(
                job=reconstructable(get_one_asset_job),
                instance=instance,
            ) as result:
                assert result.success
                defs = get_defs_for_one_asset()
                assert defs.load_asset_value("one_asset") == 1


def get_defs_for_two_assets():
    # Imagine parsing a yaml file or other arbitrary metadata format and creating
    # RemoteAsset instances
    return build_definitions_for_remote_assets(
        "two_assets_job",
        [
            remote_asset_in_script("one_asset", []),
            remote_asset_in_script("add_one_to_one_asset", ["one_asset"]),
        ],
    )


def get_two_assets_job():
    return get_defs_for_two_assets().get_job_def("two_assets_job")


def test_two_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        with instance_for_test(temp_dir=tmpdir_path) as instance:
            with execute_job(
                job=reconstructable(get_two_assets_job),
                instance=instance,
            ) as result:
                assert result.success
                defs = get_defs_for_two_assets()
                assert defs.load_asset_value("one_asset") == 1
                assert defs.load_asset_value("add_one_to_one_asset") == 2


# so this file can be loaded by dagit directly
defs = get_defs_for_two_assets()
