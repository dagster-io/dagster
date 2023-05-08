from dagster_dbt import (
    DbtCliClientResource,
    DbtCloudClientResource,
    load_assets_from_dbt_cloud_job,
    load_assets_from_dbt_project,
)

from dagster import Definitions, asset, file_relative_path, with_resources
from dagster._core.definitions import materialize
from dagster._core.instance_for_test import environ
from docs_snippets.integrations.dbt.dbt import scope_schedule_assets
from docs_snippets.integrations.dbt.dbt_cloud import (
    scope_define_instance,
    scope_schedule_dbt_cloud_assets,
)


def test_scope_schedule_assets_can_load():
    DBT_PROJECT_PATH = file_relative_path(
        __file__, "../../../assets_dbt_python/dbt_project"
    )
    DBT_PROFILES_DIR = file_relative_path(
        __file__,
        "../../../assets_dbt_python/dbt_project/config",
    )
    dbt_assets = with_resources(
        load_assets_from_dbt_project(DBT_PROJECT_PATH),
        {
            "dbt": DbtCliClientResource(
                project_dir=DBT_PROJECT_PATH,
                profiles_dir=DBT_PROFILES_DIR,
            )
        },
    )

    scope_schedule_assets(dbt_assets)


def test_scope_schedule_dbt_cloud_assets_can_load():
    dbt_cloud_instance = DbtCloudClientResource(auth_token="foo", account_id=111)
    dbt_cloud_assets = load_assets_from_dbt_cloud_job(
        dbt_cloud=dbt_cloud_instance,
        job_id=33333,
    )

    scope_schedule_dbt_cloud_assets(dbt_cloud_assets)


def test_scope_define_instance_can_load():
    with environ(
        {"DBT_CLOUD_API_TOKEN": "foo", "DBT_CLOUD_ACCOUNT_ID": "111"},
    ):
        dbt_cloud_resource_inst = scope_define_instance()

        executed = {}

        @asset
        def asset_using_dbt_cloud(dbt_cloud_resource: DbtCloudClientResource):
            assert dbt_cloud_resource.auth_token == "foo"
            assert dbt_cloud_resource.account_id == 111
            executed["yes"] = True

        assert (
            materialize(
                [asset_using_dbt_cloud],
                resources={"dbt_cloud_resource": dbt_cloud_resource_inst},
            ).success
            is True
        )

        assert executed["yes"]
