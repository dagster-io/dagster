from pathlib import Path
from unittest.mock import MagicMock

from dagster._core.code_pointer import CodePointer
from dagster._core.definitions.reconstruct import (
    ReconstructableJob,
    ReconstructableRepository,
    initialize_repository_def_from_pointer,
    reconstruct_repository_def_from_pointer,
)
from dagster._core.events import DagsterEventType
from dagster._core.execution.api import create_execution_plan, execute_plan
from dagster._core.instance_for_test import instance_for_test


def test_using_cached_asset_data_with_refresh_request(
    sign_in: MagicMock,
    get_workbooks: MagicMock,
    get_workbook: MagicMock,
    get_view: MagicMock,
    get_job: MagicMock,
    refresh_workbook: MagicMock,
    cancel_job: MagicMock,
) -> None:
    with instance_for_test() as instance:
        assert sign_in.call_count == 0
        assert get_workbooks.call_count == 0
        assert get_workbook.call_count == 0
        assert get_view.call_count == 0
        assert refresh_workbook.call_count == 0
        assert get_job.call_count == 0
        assert cancel_job.call_count == 0

        pointer = CodePointer.from_python_file(
            str(Path(__file__).parent / "definitions.py"),
            "defs",
            None,
        )
        init_repository_def = initialize_repository_def_from_pointer(
            pointer,
        )

        # 3 calls to creates the defs
        assert sign_in.call_count == 1
        assert get_workbooks.call_count == 1
        assert get_workbook.call_count == 1
        assert get_view.call_count == 0
        assert refresh_workbook.call_count == 0
        assert get_job.call_count == 0
        assert cancel_job.call_count == 0

        # 1 Tableau external assets, 2 Tableau materializable asset and 1 Dagster materializable asset
        assert len(init_repository_def.assets_defs_by_key) == 1 + 2 + 1

        repository_load_data = init_repository_def.repository_load_data

        # We use a separate file here just to ensure we get a fresh load
        recon_repository_def = reconstruct_repository_def_from_pointer(
            pointer,
            repository_load_data,
        )
        assert len(recon_repository_def.assets_defs_by_key) == 1 + 2 + 1

        # no additional calls after a fresh load
        assert sign_in.call_count == 1
        assert get_workbooks.call_count == 1
        assert get_workbook.call_count == 1
        assert get_view.call_count == 0
        assert refresh_workbook.call_count == 0
        assert get_job.call_count == 0
        assert cancel_job.call_count == 0

        # testing the job that materializes the tableau assets
        job_def = recon_repository_def.get_job("all_asset_job")
        recon_job = ReconstructableJob(
            repository=ReconstructableRepository(pointer),
            job_name="all_asset_job",
        )

        execution_plan = create_execution_plan(recon_job, repository_load_data=repository_load_data)
        run = instance.create_run_for_job(job_def=job_def, execution_plan=execution_plan)

        events = execute_plan(
            execution_plan=execution_plan,
            job=recon_job,
            dagster_run=run,
            instance=instance,
        )

        assert (
            len([event for event in events if event.event_type == DagsterEventType.STEP_SUCCESS])
            == 2
        ), "Expected two successful steps"

        # 3 calls to create the defs + 5 calls to materialize the Tableau assets
        # with 1 workbook to refresh, 1 sheet and 1 dashboard
        assert sign_in.call_count == 2
        assert get_workbooks.call_count == 1
        assert get_workbook.call_count == 1
        assert get_view.call_count == 2
        assert refresh_workbook.call_count == 1
        assert get_job.call_count == 1
        # The finish_code of the mocked get_job is 0, so no cancel_job is not called
        assert cancel_job.call_count == 0
