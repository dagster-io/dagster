from dagster import Definitions, EnvVar, asset
from dagster._core.test_utils import environ
from docs_snippets.tutorial.connecting import (
    connecting,
    connecting_with_config,
    connecting_with_envvar,
)
from docs_snippets.tutorial.connecting.resources import (
    DataGeneratorResource,
)


def test_definitions_with_resources():
    repository = connecting.defs.get_repository_def()
    resource_keys = repository.get_resource_key_mapping().values()
    assert len(resource_keys) == 3
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
