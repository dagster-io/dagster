from dagster import job, op
from dagster._core.definitions.job_definition_execution import (
    create_untainted_job_for_execution,
    job_has_execution_taint,
)


def test_execution_taint_removal() -> None:
    @op
    def an_op() -> None: ...
    @job
    def tainted_love() -> None:
        an_op()

    assert job_has_execution_taint(tainted_love)
    untainted_love = create_untainted_job_for_execution(
        job_def=tainted_love, op_selection=None, asset_selection=None, asset_check_selection=None
    )
    assert not job_has_execution_taint(untainted_love)
