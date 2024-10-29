# ruff: isort: skip_file

MANIFEST_PATH = ""


def scope_compile_dbt_manifest_with_dbt_project(manifest):
    # start_compile_dbt_manifest_with_dbt_project
    from pathlib import Path

    from dagster_dbt import DbtProject

    my_dbt_project = DbtProject(
        project_dir=Path(__file__).joinpath("..", "..", "..").resolve(),
        packaged_project_dir=Path(__file__)
        .joinpath("..", "..", "dbt-project")
        .resolve(),
    )
    my_dbt_project.prepare_if_dev()
    # end_compile_dbt_manifest_with_dbt_project


def scope_schedule_assets_dbt_only(manifest):
    from dagster import Config, RunConfig

    class MyDbtConfig(Config):
        full_refresh: bool

    # start_schedule_assets_dbt_only
    from dagster_dbt import build_schedule_from_dbt_selection, dbt_assets

    @dbt_assets(manifest=manifest)
    def my_dbt_assets(): ...

    daily_dbt_assets_schedule = build_schedule_from_dbt_selection(
        [my_dbt_assets],
        job_name="daily_dbt_models",
        cron_schedule="@daily",
        dbt_select="tag:daily",
        # If your definition of `@dbt_assets` has Dagster Configuration, you can specify it here.
        # config=RunConfig(ops={"my_dbt_assets": MyDbtConfig(full_refresh=True)}),
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
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
            return super().get_asset_key(dbt_resource_props).with_prefix("snowflake")

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_asset_key_dagster_dbt_translator


def scope_fetch_row_count() -> None:
    # start_fetch_row_count
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DbtProject, DbtCliResource, dbt_assets

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream().fetch_row_counts()

    # end_fetch_row_count


def scope_fetch_column_metadata() -> None:
    # start_fetch_column_metadata
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DbtProject, DbtCliResource, dbt_assets

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from (
            dbt.cli(["build"], context=context).stream().fetch_column_metadata()
        )

    # end_fetch_column_metadata


def scope_fetch_column_metadata_chain() -> None:
    # start_fetch_column_metadata_chain
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DbtProject, DbtCliResource, dbt_assets

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from (
            dbt.cli(["build"], context=context)
            .stream()
            .fetch_row_counts()
            .fetch_column_metadata()
        )

    # end_fetch_column_metadata_chain


def scope_custom_group_name_dagster_dbt_translator():
    # start_custom_group_name_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping, Optional

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_group_name(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[str]:
            return "snowflake"

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_group_name_dagster_dbt_translator


def scope_custom_owners_dagster_dbt_translator():
    # start_custom_owners_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping, Optional, Sequence

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_owners(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[Sequence[str]]:
            return ["owner@company.com", "team:data@company.com"]

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_owners_dagster_dbt_translator


def scope_custom_description_dagster_dbt_translator():
    # start_custom_description_dagster_dbt_translator
    import textwrap
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
            return textwrap.indent(dbt_resource_props.get("raw_sql", ""), "\t")

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_description_dagster_dbt_translator


def scope_custom_metadata_dagster_dbt_translator():
    # start_custom_metadata_dagster_dbt_translator
    from pathlib import Path
    from dagster import MetadataValue, AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_metadata(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Mapping[str, Any]:
            return {
                "dbt_metadata": MetadataValue.json(dbt_resource_props.get("meta", {}))
            }

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_metadata_dagster_dbt_translator


def scope_custom_tags_dagster_dbt_translator():
    # start_custom_tags_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_tags(self, dbt_resource_props: Mapping[str, Any]) -> Mapping[str, str]:
            dbt_tags = dbt_resource_props.get("tags", [])
            dagster_tags = {}
            for tag in dbt_tags:
                key, _, value = tag.partition("=")

                dagster_tags[key] = value if value else ""

            return dagster_tags

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_tags_dagster_dbt_translator


def scope_custom_automation_condition_dagster_dbt_translator():
    # start_custom_automation_condition_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext, AutomationCondition
    from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets
    from typing import Any, Mapping, Optional

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_automation_condition(
            self, dbt_resource_props: Mapping[str, Any]
        ) -> Optional[AutomationCondition]:
            return AutomationCondition.eager()

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_custom_automation_condition_dagster_dbt_translator


def scope_disable_asset_check_dagster_dbt_translator():
    # start_disable_asset_check_dagster_dbt_translator
    from pathlib import Path
    from dagster import AssetExecutionContext
    from dagster_dbt import (
        DagsterDbtTranslator,
        DagsterDbtTranslatorSettings,
        DbtCliResource,
        DbtProject,
        dbt_assets,
    )

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))
    dagster_dbt_translator = DagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_asset_checks=False)
    )

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        dagster_dbt_translator=dagster_dbt_translator,
    )
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    # end_disable_asset_check_dagster_dbt_translator


def scope_config_dbt_assets():
    # start_config_dbt_assets
    from pathlib import Path

    from dagster import AssetExecutionContext, Config
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    class MyDbtConfig(Config):
        full_refresh: bool

    @dbt_assets(manifest=my_dbt_project.manifest_path)
    def my_dbt_assets(
        context: AssetExecutionContext, dbt: DbtCliResource, config: MyDbtConfig
    ):
        dbt_build_args = ["build"]
        if config.full_refresh:
            dbt_build_args += ["--full-refresh"]

        yield from dbt.cli(dbt_build_args, context=context).stream()

    # end_config_dbt_assets

    # start_config_dbt_job
    from dagster import RunConfig, define_asset_job
    from dagster_dbt import build_dbt_asset_selection

    my_job = define_asset_job(
        name="all_dbt_assets",
        selection=build_dbt_asset_selection(
            [my_dbt_assets],
        ),
        config=RunConfig(
            ops={"my_dbt_assets": MyDbtConfig(full_refresh=True, seed=True)}
        ),
    )

    # end_config_dbt_job


def scope_build_incremental_model():
    # start_build_incremental_model
    import json
    from pathlib import Path

    from dagster import DailyPartitionsDefinition, OpExecutionContext
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    my_dbt_project = DbtProject(project_dir=Path("path/to/dbt_project"))

    @dbt_assets(
        manifest=my_dbt_project.manifest_path,
        partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    )
    def partitionshop_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
        start, end = context.partition_time_window

        dbt_vars = {"min_date": start.isoformat(), "max_date": end.isoformat()}
        dbt_build_args = ["build", "--vars", json.dumps(dbt_vars)]

        yield from dbt.cli(dbt_build_args, context=context).stream()

    # end_build_incremental_model


def scope_use_dbt_defer_with_dbt_project(manifest):
    # start_use_dbt_defer_with_dbt_project
    import os
    from pathlib import Path

    from dagster import AssetExecutionContext
    from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

    my_dbt_project = DbtProject(
        project_dir=Path(__file__).joinpath("..", "..", "..").resolve(),
        packaged_project_dir=Path(__file__)
        .joinpath("..", "..", "dbt-project")
        .resolve(),
        state_path=Path("state"),
    )
    my_dbt_project.prepare_if_dev()

    @dbt_assets(manifest=my_dbt_project.manifest_path)
    def my_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        yield from dbt.cli(["build", *dbt.get_defer_args()], context=context).stream()

    # end_use_dbt_defer_with_dbt_project
