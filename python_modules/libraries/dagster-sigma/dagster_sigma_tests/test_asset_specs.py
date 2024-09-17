from pathlib import Path

import responses
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_loader import DefinitionsLoadType
from dagster._core.definitions.reconstruct import repository_def_from_pointer
from dagster._core.instance_for_test import instance_for_test


@responses.activate
def test_load_assets_organization_data(sigma_auth_token: str, sigma_sample_data: None) -> None:
    with instance_for_test() as _instance:
        # first, we resolve the repository to generate our cached metadata
        repository_def = repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "pending_repo.py"), "defs", None
            ),
            DefinitionsLoadType.INITIALIZATION,
            None,
        )

        # 2 Sigma external assets, one materializable asset
        assert len(repository_def.assets_defs_by_key) == 2 + 1

        workbook_key = AssetKey("Sample_Workbook")
        assert repository_def.assets_defs_by_key[workbook_key].owners_by_key[workbook_key] == [
            "ben@dagsterlabs.com"
        ]

        calls = len(responses.calls)

        # Attempt to reconstruct - this should not call the expensive fetch functions
        # Responses will error if we do, since the mocked endpoints are only set up to be called once
        data = repository_def.repository_load_data

        # We use a separate file here just to ensure we get a fresh load
        recon_repository_def = repository_def_from_pointer(
            CodePointer.from_python_file(
                str(Path(__file__).parent / "pending_repo_2.py"), "defs", None
            ),
            DefinitionsLoadType.RECONSTRUCTION,
            data,
        )
        assert len(recon_repository_def.assets_defs_by_key) == 2 + 1

        assert len(responses.calls) == calls
