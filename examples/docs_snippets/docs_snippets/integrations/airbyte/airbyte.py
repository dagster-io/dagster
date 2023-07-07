# ruff: isort: skip_file


def scope_define_instance():
    # start_define_instance
    from dagster import EnvVar
    from dagster_airbyte import AirbyteResource

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
        # If using basic auth, include username and password:
        username="airbyte",
        password=EnvVar("AIRBYTE_PASSWORD"),
    )
    # end_define_instance


def scope_define_cloud_instance() -> None:
    # start_define_cloud_instance
    from dagster import EnvVar
    from dagster_airbyte import AirbyteCloudResource

    airbyte_instance = AirbyteCloudResource(
        api_key=EnvVar("AIRBYTE_API_KEY"),
    )
    # end_define_cloud_instance


def scope_load_assets_from_airbyte_project():
    # start_load_assets_from_airbyte_project
    from dagster_airbyte import load_assets_from_airbyte_project

    airbyte_assets = load_assets_from_airbyte_project(
        project_dir="path/to/airbyte/project",
    )
    # end_load_assets_from_airbyte_project


def scope_load_assets_from_airbyte_instance():
    from dagster_airbyte import AirbyteResource
    from dagster import EnvVar

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
        # If using basic auth, include username and password:
        username="airbyte",
        password=EnvVar("AIRBYTE_PASSWORD"),
    )
    # start_load_assets_from_airbyte_instance
    from dagster_airbyte import load_assets_from_airbyte_instance

    # Use the airbyte_instance resource we defined in Step 1
    airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)
    # end_load_assets_from_airbyte_instance


def scope_airbyte_project_config():
    from dagster_airbyte import AirbyteResource

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
    )
    # start_airbyte_project_config
    from dagster_airbyte import load_assets_from_airbyte_project

    from dagster import with_resources

    # Use the airbyte_instance resource we defined in Step 1
    airbyte_assets = with_resources(
        [load_assets_from_airbyte_project(project_dir="path/to/airbyte/project")],
        {"airbyte": airbyte_instance},
    )
    # end_airbyte_project_config


def scope_manually_define_airbyte_assets():
    # start_manually_define_airbyte_assets
    from dagster_airbyte import build_airbyte_assets

    airbyte_assets = build_airbyte_assets(
        connection_id="87b7fe85-a22c-420e-8d74-b30e7ede77df",
        destination_tables=["releases", "tags", "teams", "stargazers"],
    )
    # end_manually_define_airbyte_assets


def scope_manually_define_airbyte_assets_cloud():
    # start_manually_define_airbyte_assets_cloud
    from dagster_airbyte import build_airbyte_assets

    airbyte_assets = build_airbyte_assets(
        connection_id="43908042-8399-4a58-82f1-71a45099fff7",
        destination_tables=["releases", "tags", "teams"],
    )
    # end_manually_define_airbyte_assets_cloud


def scope_airbyte_manual_config():
    # start_airbyte_manual_config
    from dagster_airbyte import build_airbyte_assets, AirbyteResource

    from dagster import with_resources

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
    )
    airbyte_assets = with_resources(
        build_airbyte_assets(
            connection_id="87b7fe85-a22c-420e-8d74-b30e7ede77df",
            destination_tables=["releases", "tags", "teams", "stargazers"],
        ),
        # Use the airbyte_instance resource we defined in Step 1
        {"airbyte": airbyte_instance},
    )
    # end_airbyte_manual_config


def scope_airbyte_cloud_manual_config():
    # start_airbyte_cloud_manual_config
    from dagster_airbyte import build_airbyte_assets, AirbyteCloudResource

    from dagster import Definitions, EnvVar

    airbyte_instance = AirbyteCloudResource(
        api_key=EnvVar("AIRBYTE_API_KEY"),
    )
    airbyte_assets = build_airbyte_assets(
        connection_id="43908042-8399-4a58-82f1-71a45099fff7",
        destination_tables=["releases", "tags", "teams"],
    )

    defs = Definitions(assets=[airbyte_assets], resources={"airbyte": airbyte_instance})
    # end_airbyte_cloud_manual_config


def scope_add_downstream_assets():
    import mock

    with mock.patch("dagster_snowflake_pandas.SnowflakePandasIOManager"):
        # start_add_downstream_assets
        import json
        from dagster import asset, Definitions, define_asset_job, AssetSelection
        from dagster_airbyte import load_assets_from_airbyte_instance, AirbyteResource
        from dagster_snowflake_pandas import SnowflakePandasIOManager
        import pandas as pd

        airbyte_instance = AirbyteResource(
            host="localhost",
            port="8000",
        )

        airbyte_assets = load_assets_from_airbyte_instance(
            airbyte_instance,
            io_manager_key="snowflake_io_manager",
        )

        @asset
        def stargazers_file(stargazers: pd.DataFrame):
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = define_asset_job(
            "my_upstream_job",
            AssetSelection.keys("stargazers_file")
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={"snowflake_io_manager": SnowflakePandasIOManager(...)},
        )

        # end_add_downstream_assets


def scope_add_downstream_assets_cloud():
    import mock

    with mock.patch("dagster_snowflake_pandas.SnowflakePandasIOManager"):
        # start_add_downstream_assets_cloud
        import json
        from dagster import asset, Definitions, define_asset_job, AssetSelection, EnvVar
        from dagster_airbyte import (
            build_airbyte_assets,
            AirbyteCloudResource,
        )
        from dagster_snowflake_pandas import SnowflakePandasIOManager
        import pandas as pd

        airbyte_instance = AirbyteCloudResource(
            api_key=EnvVar("AIRBYTE_API_KEY"),
        )
        airbyte_assets = build_airbyte_assets(
            connection_id="43908042-8399-4a58-82f1-71a45099fff7",
            destination_tables=["releases", "tags", "teams"],
        )

        @asset
        def stargazers_file(stargazers: pd.DataFrame):
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = define_asset_job(
            "my_upstream_job",
            AssetSelection.keys("stargazers_file")
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={
                "snowflake_io_manager": SnowflakePandasIOManager(...),
                "airbyte_instance": airbyte_instance,
            },
        )

        # end_add_downstream_assets_cloud


def scope_schedule_assets():
    from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance

    # start_schedule_assets
    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
    )
    airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)

    from dagster import (
        ScheduleDefinition,
        define_asset_job,
        AssetSelection,
        Definitions,
    )

    # materialize all assets
    run_everything_job = define_asset_job("run_everything", selection="*")

    # only run my_airbyte_connection and downstream assets
    my_etl_job = define_asset_job(
        "my_etl_job", AssetSelection.groups("my_airbyte_connection").downstream()
    )

    defs = Definitions(
        assets=[airbyte_assets],
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


def scope_schedule_assets_cloud():
    # start_schedule_assets_cloud
    from dagster_airbyte import AirbyteCloudResource, build_airbyte_assets

    from dagster import (
        EnvVar,
        ScheduleDefinition,
        define_asset_job,
        Definitions,
    )

    airbyte_instance = AirbyteCloudResource(
        api_key=EnvVar("AIRBYTE_API_KEY"),
    )
    airbyte_assets = build_airbyte_assets(
        connection_id="43908042-8399-4a58-82f1-71a45099fff7",
        destination_tables=["releases", "tags", "teams"],
    )

    # materialize all assets
    run_everything_job = define_asset_job("run_everything", selection="*")

    defs = Definitions(
        assets=[airbyte_assets],
        schedules=[
            ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ],
        resources={"airbyte": airbyte_instance},
    )

    # end_schedule_assets_cloud
