# ruff: isort: skip_file

MANIFEST_PATH = ""


def scope_compile_dbt_manifest(manifest):
    # start_compile_dbt_manifest
    import os
    from pathlib import Path

    from dagster_dbt import DbtCliResource

    dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
    dbt = DbtCliResource(project_dir=os.fspath(dbt_project_dir))

    # If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at runtime.
    # Otherwise, we expect a manifest to be present in the project's target directory.
    if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"):
        dbt_manifest_path = (
            dbt.cli(
                ["--quiet", "parse"],
                target_path=Path("target"),
            )
            .wait()
            .target_path.joinpath("manifest.json")
        )
    else:
        dbt_manifest_path = dbt_project_dir.joinpath("target", "manifest.json")
    # end_compile_dbt_manifest


def scope_schedule_assets_dbt_only(manifest):
    # start_schedule_assets_dbt_only
    from dagster_dbt import build_schedule_from_dbt_selection, dbt_assets

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(): ...

    daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name="daily_dbt_models",
        cron_schedule="@daily",
        dbt_select="tag:daily",
    )
    # end_schedule_assets_dbt_only


def scope_schedule_assets_dbt_and_downstream(manifest):
    # start_schedule_assets_dbt_downstream
    from dagster import define_asset_job, ScheduleDefinition
    from dagster_dbt import build_dbt_asset_selection, dbt_assets

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(): ...

    # selects all models tagged with "daily", and all their downstream asset dependencies
    daily_selection = build_dbt_asset_selection(
        [my_dbt_assets], dbt_select="tag:daily"
    ).downstream()

    daily_dbt_assets_and_downstream_schedule = ScheduleDefinition(
        job=define_asset_job("daily_assets", selection=daily_selection),
        cron_schedule="@daily",
    )

    # end_schedule_assets_dbt_downstream


def scope_downstream_asset():
    from dagster import AssetExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

    # start_downstream_asset
    from dagster_dbt import get_asset_key_for_model
    from dagster import asset

    @asset(deps=[get_asset_key_for_model([my_dbt_assets], "my_dbt_model")])
    def my_downstream_asset(): ...

    # end_downstream_asset_pandas_df_manager


def scope_downstream_asset_pandas_df_manager():
    from dagster import AssetExecutionContext, DbtCliResource
    from dagster_dbt import dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

    # start_downstream_asset_pandas_df_manager
    from dagster_dbt import get_asset_key_for_model
    from dagster import AssetIn, asset

    @asset(
        ins={
            "my_dbt_model": AssetIn(
                input_manager_key="pandas_df_manager",
                key=get_asset_key_for_model([my_dbt_assets], "my_dbt_model"),
            )
        },
    )
    def my_downstream_asset(my_dbt_model):
        # my_dbt_model is a Pandas dataframe
        return my_dbt_model.where(foo="bar")

    # end_downstream_asset_pandas_df_manager


def scope_upstream_asset():
    # start_upstream_asset
    from dagster import asset, AssetExecutionContext
    from dagster_dbt import DbtCliResource, get_asset_key_for_source, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

    @asset(key=get_asset_key_for_source([my_dbt_assets], "jaffle_shop"))
    def orders():
        return ...

    # end_upstream_asset


def scope_upstream_multi_asset():
    from dagster import AssetExecutionContext
    from dagster_dbt import DbtCliResource, dbt_assets

    @dbt_assets(manifest=MANIFEST_PATH)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

    # start_upstream_multi_asset
    from dagster import multi_asset, AssetOut, Output
    from dagster_dbt import get_asset_keys_by_output_name_for_source

    @multi_asset(
        outs={
            name: AssetOut(key=asset_key)
            for name, asset_key in get_asset_keys_by_output_name_for_source(
                [my_dbt_assets], "jaffle_shop"
            ).items()
        }
    )
    def jaffle_shop(context: AssetExecutionContext):
        output_names = list(context.op_execution_context.selected_output_names)
        yield Output(value=..., output_name=output_names[0])
        yield Output(value=..., output_name=output_names[1])

    # end_upstream_multi_asset


def scope_existing_asset():
    # start_upstream_dagster_asset
    from dagster import asset

    @asset
    def upstream(): ...

    # end_upstream_dagster_asset


def scope_custom_asset_key_dagster_dbt_translator():
    # start_custom_asset_key_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetKey, AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            return super().get_asset_key(dbt_resource_props).with_prefix("snowflake")

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_asset_key_dagster_dbt_translator


def scope_custom_group_name_dagster_dbt_translator():
    # start_custom_group_name_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping, Optional

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_group_name(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[str]:
            return "snowflake"

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_group_name_dagster_dbt_translator


def scope_custom_description_dagster_dbt_translator():
    # start_custom_description_dagster_dbt_translator
    import textwrap
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
            return textwrap.indent(dbt_resource_props.get("raw_sql", ""), "\t")

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_description_dagster_dbt_translator


def scope_custom_metadata_dagster_dbt_translator():
    # start_custom_metadata_dagster_dbt_translator
    from pathlib import Path
    from dagster import MetadataValue, AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_metadata(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Mapping[str, Any]:
            return {
                "dbt_metadata": MetadataValue.json(dbt_resource_props.get("meta", {}))
            }

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_metadata_dagster_dbt_translator


def scope_custom_tags_dagster_dbt_translator():
    # start_custom_tags_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
            dbt_tags = dbt_resource_props.get("tags", [])
            dagster_tags = {}
            for tag in dbt_tags:
                key, _, value = tag.partition("=")

                dagster_tags[key] = value if value else "__dagster_no_value"

            return dagster_tags

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_tags_dagster_dbt_translator


def scope_custom_auto_materialize_policy_dagster_dbt_translator():
    # start_custom_auto_materialize_policy_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext, AutoMaterializePolicy
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping, Optional

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_auto_materialize_policy(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[AutoMaterializePolicy]:
            return AutoMaterializePolicy.eager()

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_auto_materialize_policy_dagster_dbt_translator


def scope_custom_freshness_policy_dagster_dbt_translator():
    # start_custom_freshness_policy_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext, FreshnessPolicy
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets
    from typing import Any, Mapping, Optional

    manifest_path = Path("path/to/dbt_project/target/manifest.json")

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_freshness_policy(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[FreshnessPolicy]:
            return FreshnessPolicy(maximum_lag_minutes=60)

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_freshness_policy_dagster_dbt_translator


def scope_enable_asset_check_dagster_dbt_translator():
    # start_enable_asset_check_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import (
        DagsterDbtTranslator,
        DagsterDbtTranslatorSettings,
        DbtCliResource,
        dbt_assets,
    )

    manifest_path = Path("path/to/dbt_project/target/manifest.json")
    dagster_dbt_translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=True)
    )

    @dbt_assets(
        manifest=manifest_path,
        dagster_dbt_translator=dagster_dbt_translator,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_enable_asset_check_dagster_dbt_translator
