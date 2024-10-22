from pathlib import Path
from unittest.mock import MagicMock

from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.definitions_load_context import DefinitionsLoadType
from dagster._core.definitions.reconstruct import repository_def_from_pointer


def test_using_cached_asset_data(
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
    get_view: MagicMock,
) -> None:
    assert sign_in.call_count == 0
    assert get_workbooks.call_count == 0
    assert get_workbook.call_count == 0
    assert get_view.call_count == 0

    from dagster_tableau_tests.repos.definitions import defs

    # 3 calls to creates the defs
    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert get_view.call_count == 0

    # 1 Tableau external assets, 2 Tableau materializable asset and 1 Dagster materializable asset
    assert len(defs.get_repository_def().assets_defs_by_key) == 1 + 2 + 1

    # job_def = defs.get_job_def("all_asset_job")
    repository_load_data = defs.get_repository_def().repository_load_data

    # We use a separate file here just to ensure we get a fresh load
    recon_repository_def = repository_def_from_pointer(
        CodePointer.from_python_file(
            str(Path(__file__).parent / "repos/definitions.py"), "defs", None
        ),
        DefinitionsLoadType.RECONSTRUCTION,
        repository_load_data,
    )
    assert len(recon_repository_def.assets_defs_by_key) == 1 + 2 + 1

    # TODO fix to test defs like in PR #24385
    # no additional calls
    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert get_view.call_count == 0


def test_using_cached_asset_data_with_refresh_request(
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
    get_view: MagicMock,
    get_job: MagicMock,
    refresh_workbook: MagicMock,
    cancel_job: MagicMock,
) -> None:
    assert sign_in.call_count == 0
    assert get_workbooks.call_count == 0
    assert get_workbook.call_count == 0
    assert get_view.call_count == 0
    assert refresh_workbook.call_count == 0
    assert get_job.call_count == 0
    assert cancel_job.call_count == 0

    from dagster_tableau_tests.repos.definitions_with_refreshable_workbook_ids import defs

    # 3 calls to creates the defs
    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert get_view.call_count == 0
    assert refresh_workbook.call_count == 0
    assert get_job.call_count == 0
    assert cancel_job.call_count == 0

    # 1 Tableau external assets, 2 Tableau materializable asset and 1 Dagster materializable asset
    assert len(defs.get_repository_def().assets_defs_by_key) == 1 + 2 + 1

    # job_def = defs.get_job_def("all_asset_job")
    repository_load_data = defs.get_repository_def().repository_load_data

    # We use a separate file here just to ensure we get a fresh load
    recon_repository_def = repository_def_from_pointer(
        CodePointer.from_python_file(
            str(Path(__file__).parent / "repos/definitions_with_refreshable_workbook_ids.py"),
            "defs",
            None,
        ),
        DefinitionsLoadType.RECONSTRUCTION,
        repository_load_data,
    )
    assert len(recon_repository_def.assets_defs_by_key) == 1 + 2 + 1

    # TODO fix to test refresh request like in PR #24862
    # no additional calls
    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert get_view.call_count == 0
    assert refresh_workbook.call_count == 0
    assert get_job.call_count == 0
    assert cancel_job.call_count == 0
