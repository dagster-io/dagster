from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import responses
from click.testing import CliRunner
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.reconstruct import (
    initialize_repository_def_from_pointer,
    reconstruct_repository_def_from_pointer,
)
from dagster._core.instance_for_test import instance_for_test
from dagster._utils.env import environ


@responses.activate
def test_snapshot_cli_rehydrate(sigma_auth_token: str, sigma_sample_data: None) -> None:
    with instance_for_test() as _instance, TemporaryDirectory() as temp_dir:
        from dagster_sigma.cli import sigma_snapshot_command

        temp_file = Path(temp_dir) / "snapshot.snap"
        out = CliRunner().invoke(
            sigma_snapshot_command,
            args=[
                "-f",
                str(Path(__file__).parent / "pending_repo_snapshot.py"),
                "--output-path",
                str(temp_file),
            ],
        )
        assert out.exit_code == 0

        calls = len(responses.calls)
        # Ensure that we can reconstruct the repository from the snapshot without making any calls
        with environ({"SIGMA_SNAPSHOT_PATH": str(temp_file)}):
            repository_def = initialize_repository_def_from_pointer(
                CodePointer.from_python_file(
                    str(Path(__file__).parent / "pending_repo_snapshot.py"), "defs", None
                ),
            )
            assert len(repository_def.assets_defs_by_key) == 2 + 1

            assert len(responses.calls) == calls


@responses.activate
def test_load_assets_organization_data(sigma_auth_token: str, sigma_sample_data: None) -> None:
    with instance_for_test() as _instance:
        # first, we resolve the repository to generate our cached metadata
        repository_def = initialize_repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "pending_repo.py"), "defs", None
            ),
        )

        # 2 Sigma external assets, one materializable asset
        assert len(repository_def.assets_defs_by_key) == 2 + 1

        # No longer fetch owner for now, since this can be expensive
        # workbook_key = AssetKey("Sample_Workbook")
        # assert repository_def.assets_defs_by_key[workbook_key].owners_by_key[workbook_key] == [
        #     "ben@dagsterlabs.com"
        # ]

        calls = len(responses.calls)

        # Attempt to reconstruct - this should not call the expensive fetch functions
        # Responses will error if we do, since the mocked endpoints are only set up to be called once
        data = repository_def.repository_load_data

        # We use a separate file here just to ensure we get a fresh load
        recon_repository_def = reconstruct_repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "pending_repo_2.py"), "defs", None
            ),
            data,
        )
        assert len(recon_repository_def.assets_defs_by_key) == 2 + 1

        assert len(responses.calls) == calls


@responses.activate
def test_materialize_workbook(
    sigma_auth_token: str, sigma_sample_data: None, sigma_materialization: None
) -> None:
    with instance_for_test() as _instance:
        # first, we resolve the repository to generate our cached metadata
        repository_def = initialize_repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "materialize_workbook.py"), "defs", None
            ),
        )

        workbook_asset = repository_def.assets_defs_by_key[AssetKey(["Sample_Workbook"])]
        assert workbook_asset.is_materializable

        # materialize the workbook
        with environ({"SIGMA_CLIENT_ID": "fake", "SIGMA_CLIENT_SECRET": "fake"}):
            result = materialize([workbook_asset], raise_on_error=False)
            assert result.success


@responses.activate
def test_load_assets_organization_data_translator(
    sigma_auth_token: str, sigma_sample_data: None
) -> None:
    with instance_for_test() as _instance:
        repository_def = initialize_repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "pending_repo_with_translator.py"), "defs", None
            ),
        )

        assert len(repository_def.assets_defs_by_key) == 2
        assert all(
            key.path[0] == "my_prefix" for key in repository_def.assets_defs_by_key.keys()
        ), repository_def.assets_defs_by_key


@responses.activate
def test_load_assets_organization_data_translator_legacy(
    sigma_auth_token: str, sigma_sample_data: None
) -> None:
    with instance_for_test() as _instance:
        with pytest.warns(
            DeprecationWarning,
            match=r"Support of `dagster_sigma_translator` as a Type\[DagsterSigmaTranslator\]",
        ):
            repository_def = initialize_repository_def_from_pointer(
                CodePointer.from_python_file(
                    str(Path(__file__).parent / "pending_repo_with_translator_legacy.py"),
                    "defs",
                    None,
                ),
            )

        assert len(repository_def.assets_defs_by_key) == 2
        assert all(
            key.path[0] == "my_prefix" for key in repository_def.assets_defs_by_key.keys()
        ), repository_def.assets_defs_by_key
