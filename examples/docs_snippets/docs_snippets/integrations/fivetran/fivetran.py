# ruff: isort: skip_file


def scope_define_instance():
    # start_define_instance
    from dagster_fivetran import FivetranResource
    from dagster import EnvVar

    # Pull API key and secret from environment variables
    fivetran_instance = FivetranResource(
        api_key=EnvVar("FIVETRAN_API_KEY"),
        api_secret=EnvVar("FIVETRAN_API_SECRET"),
    )
    # end_define_instance


def scope_load_assets_from_fivetran_instance():
    from dagster_fivetran import FivetranResource
    from dagster import EnvVar

    fivetran_instance = FivetranResource(
        api_key=EnvVar("FIVETRAN_API_KEY"),
        api_secret=EnvVar("FIVETRAN_API_SECRET"),
    )
    # start_load_assets_from_fivetran_instance
    from dagster_fivetran import load_assets_from_fivetran_instance

    # Use the fivetran_instance resource we defined in Step 1
    fivetran_assets = load_assets_from_fivetran_instance(fivetran_instance)
    # end_load_assets_from_fivetran_instance


def scope_manually_define_fivetran_assets():
    # start_manually_define_fivetran_assets
    from dagster_fivetran import build_fivetran_assets

    fivetran_assets = build_fivetran_assets(
        connector_id="omit_constitutional",
        destination_tables=["public.survey_responses", "public.surveys"],
    )
    # end_manually_define_fivetran_assets


def scope_fivetran_manual_config():
    from dagster_fivetran import FivetranResource
    from dagster import EnvVar

    fivetran_instance = FivetranResource(
        api_key=EnvVar("FIVETRAN_API_KEY"),
        api_secret=EnvVar("FIVETRAN_API_SECRET"),
    )
    # start_fivetran_manual_config
    from dagster_fivetran import build_fivetran_assets

    from dagster import with_resources

    fivetran_assets = with_resources(
        build_fivetran_assets(
            connector_id="omit_constitutional",
            destination_tables=["public.survey_responses", "public.surveys"],
        ),
        # Use the fivetran_instance resource we defined in Step 1
        {"fivetran": fivetran_instance},
    )
    # end_fivetran_manual_config


def scope_schedule_assets():
    # start_schedule_assets
    from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance
    from dagster import (
        ScheduleDefinition,
        define_asset_job,
        AssetSelection,
        EnvVar,
        Definitions,
    )

    fivetran_instance = FivetranResource(
        api_key=EnvVar("FIVETRAN_API_KEY"),
        api_secret=EnvVar("FIVETRAN_API_SECRET"),
    )
    fivetran_assets = load_assets_from_fivetran_instance(fivetran_instance)

    # materialize all assets
    run_everything_job = define_asset_job("run_everything", selection="*")

    # only run my_fivetran_connection and downstream assets
    my_etl_job = define_asset_job(
        "my_etl_job", AssetSelection.groups("my_fivetran_connection").downstream()
    )

    defs = Definitions(
        assets=[fivetran_assets],
        schedules=[
            ScheduleDefinition(
                job=my_etl_job,
                cron_schedule="@daily",
            ),
            ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ],
    )
    # end_schedule_assets


def scope_add_downstream_assets():
    import mock

    with mock.patch("dagster_snowflake_pandas.SnowflakePandasIOManager"):
        # start_add_downstream_assets
        import json

        from dagster_fivetran import (
            FivetranResource,
            load_assets_from_fivetran_instance,
        )
        from dagster import (
            ScheduleDefinition,
            define_asset_job,
            asset,
            AssetIn,
            AssetKey,
            Definitions,
            AssetSelection,
            EnvVar,
            Definitions,
        )
        from dagster_snowflake_pandas import SnowflakePandasIOManager

        fivetran_instance = FivetranResource(
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        fivetran_assets = load_assets_from_fivetran_instance(
            fivetran_instance,
            io_manager_key="snowflake_io_manager",
        )

        @asset(
            ins={
                "survey_responses": AssetIn(
                    key=AssetKey(["public", "survey_responses"])
                )
            }
        )
        def survey_responses_file(survey_responses):
            with open("survey_responses.json", "w", encoding="utf8") as f:
                f.write(json.dumps(survey_responses, indent=2))

        # only run the airbyte syncs necessary to materialize survey_responses_file
        my_upstream_job = define_asset_job(
            "my_upstream_job",
            AssetSelection.keys("survey_responses_file")
            .upstream()  # all upstream assets (in this case, just the survey_responses Fivetran asset)
            .required_multi_asset_neighbors(),  # all Fivetran assets linked to the same connection
        )

        defs = Definitions(
            jobs=[my_upstream_job],
            assets=[fivetran_assets, survey_responses_file],
            resources={"snowflake_io_manager": SnowflakePandasIOManager(...)},
        )
        # end_add_downstream_assets
