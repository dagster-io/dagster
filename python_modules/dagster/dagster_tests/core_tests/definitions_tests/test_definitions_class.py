from dagster import Definitions, asset, ResourceDefinition


def get_all_assets_from_repo(repo):
    # could not find public method on repository to do this
    return list(repo._assets_defs_by_key.values())  # pylint: disable=protected-access


def test_basic_asset():
    assert Definitions

    @asset
    def an_asset():
        pass

    repo = Definitions(assets=[an_asset])

    all_assets = get_all_assets_from_repo(repo)
    assert len(all_assets) == 1
    assert all_assets[0].key.to_user_string() == "an_asset"


def test_with_resource_binding():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "wrapped"
        executed["yes"] = True

    repo = Definitions(
        assets=[requires_foo],
        resources={"foo": ResourceDefinition.hardcoded_resource("wrapped")},
    )
    asset_job = repo.get_all_jobs()[0]  # type: ignore
    asset_job.execute_in_process()
    assert executed["yes"]


def test_resource_coercion():
    executed = {}

    @asset(required_resource_keys={"foo"})
    def requires_foo(context):
        assert context.resources.foo == "object-to-coerce"
        executed["yes"] = True

    repo = Definitions(
        assets=[requires_foo],
        resources={"foo": "object-to-coerce"},
    )
    asset_job = repo.get_all_jobs()[0]  # type: ignore
    asset_job.execute_in_process()
    assert executed["yes"]
