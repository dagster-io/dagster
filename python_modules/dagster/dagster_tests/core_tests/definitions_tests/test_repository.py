from dagster import AssetKey, repository, resource
from dagster.core.asset_defs import AssetIn, asset


def test_asset_repository_bare():
    @asset
    def asset_foo():
        return "foo"

    @asset
    def asset_bar():
        return "bar"

    @asset(
        ins={"asset_bar": AssetIn(asset_key=AssetKey("asset_foo"))}
    )  # should still use output from asset_foo
    def last_asset(asset_bar):
        return asset_bar

    @repository
    def the_repo():
        return [asset_foo, asset_bar, last_asset]

    mega_job = the_repo.get_all_jobs()[0]
    assert mega_job.name == "__REPOSITORY_MEGA_JOB"


def test_repository_resources():
    @asset(required_resource_keys={"the_resource"})
    def asset_foo():
        return "foo"

    @resource
    def the_resource():
        pass

    @repository(resource_defs={"the_resource": the_resource})
    def the_repo():
        return [asset_foo]

    mega_job = the_repo.get_all_jobs()[0]
    assert mega_job.name == "__REPOSITORY_MEGA_JOB"
