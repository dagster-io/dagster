from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.decorators.repository_decorator import repository
from dagster._core.definitions.decorators.schedule_decorator import schedule
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job

def _get_repo():
    @asset
    def foo():
        return True

    @asset
    def bar(foo):  # pylint: disable=unused-argument
        return True

    all_job = define_asset_job("all_job", AssetSelection.all())

    @schedule(job_name="all_job", cron_schedule="* * * * *")
    def stale_assets_schedule(context):
        return RunRequest(
            job_name="all_job",
            stale_only=True,
        )

    @repository
    def repo():
        return [all_job, foo, bar]

    return repo
