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

    from dagster_tableau_tests.definitions import defs

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
        CodePointer.from_python_file(str(Path(__file__).parent / "definitions.py"), "defs", None),
        DefinitionsLoadType.RECONSTRUCTION,
        repository_load_data,
    )
    assert len(recon_repository_def.assets_defs_by_key) == 1 + 2 + 1

    # no additional calls
    assert sign_in.call_count == 1
    assert get_workbooks.call_count == 1
    assert get_workbook.call_count == 1
    assert get_view.call_count == 0
