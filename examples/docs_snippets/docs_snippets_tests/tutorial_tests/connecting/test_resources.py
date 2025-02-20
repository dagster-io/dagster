from dagster import Definitions, EnvVar, asset
from dagster._core.test_utils import environ
from docs_snippets.tutorial.connecting import connecting
from docs_snippets.tutorial.connecting.resources import DataGeneratorResource


def test_definitions_with_resources() -> None:
    repository = connecting.defs.get_repository_def()
    resource_keys = repository.get_top_level_resources()
    assert len(resource_keys) == 1
    assert "hackernews_api" in resource_keys


def test_resources_with_config():
    executed = {}

    NUM_DAYS = 365

    @asset
    def test_asset(datagen: DataGeneratorResource):
        assert datagen.num_days == NUM_DAYS
        executed["yes"] = True

    defs = Definitions(
        assets=[test_asset],
        resources={
            "datagen": DataGeneratorResource(
                num_days=NUM_DAYS,
            )
        },
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert executed["yes"]


def test_resources_with_env_var():
    with environ({"HACKERNEWS_NUM_DAYS_WINDOW": "5"}):
        executed = {}

        @asset
        def test_asset(datagen: DataGeneratorResource):
            assert datagen.num_days == 5
            executed["yes"] = True

        defs = Definitions(
            assets=[test_asset],
            resources={
                "datagen": DataGeneratorResource(
                    num_days=EnvVar.int("HACKERNEWS_NUM_DAYS_WINDOW"),
                )
            },
        )

        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
        assert executed["yes"]
