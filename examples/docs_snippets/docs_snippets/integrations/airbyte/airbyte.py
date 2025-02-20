# ruff: isort: skip_file


def scope_define_instance():
    # start_define_instance
    import dagster as dg
    from dagster_airbyte import AirbyteResource

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
        # If using basic auth, include username and password:
        username="airbyte",
        password=dg.EnvVar("AIRBYTE_PASSWORD"),
    )
    # end_define_instance


def scope_define_cloud_instance() -> None:
    # start_define_cloud_instance
    import dagster as dg
    from dagster_airbyte import AirbyteCloudResource

    airbyte_instance = AirbyteCloudResource(
        client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
        client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
    )
    # end_define_cloud_instance


def scope_load_assets_from_airbyte_instance():
    import dagster as dg
    from dagster_airbyte import AirbyteResource

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
        # If using basic auth, include username and password:
        username="airbyte",
        password=dg.EnvVar("AIRBYTE_PASSWORD"),
    )
    # start_load_assets_from_airbyte_instance
    from dagster_airbyte import load_assets_from_airbyte_instance

    # Use the airbyte_instance resource we defined in Step 1
    airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)
    # end_load_assets_from_airbyte_instance


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
    import dagster as dg

    from dagster_airbyte import build_airbyte_assets, AirbyteResource

    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
    )
    airbyte_assets = dg.with_resources(
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
    import dagster as dg

    from dagster_airbyte import build_airbyte_assets, AirbyteCloudResource

    airbyte_instance = AirbyteCloudResource(
        client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
        client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
    )
    airbyte_assets = build_airbyte_assets(
        connection_id="43908042-8399-4a58-82f1-71a45099fff7",
        destination_tables=["releases", "tags", "teams"],
    )

    defs = dg.Definitions(
        assets=airbyte_assets, resources={"airbyte": airbyte_instance}
    )
    # end_airbyte_cloud_manual_config


def scope_add_downstream_assets():
    from unittest import mock

    with mock.patch("dagster_snowflake_pandas.SnowflakePandasIOManager"):
        # start_add_downstream_assets
        import json
        import dagster as dg

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

        @dg.asset
        def stargazers_file(stargazers: pd.DataFrame):
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = dg.define_asset_job(
            "my_upstream_job",
            dg.AssetSelection.assets(stargazers_file)
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte dg.asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = dg.Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={"snowflake_io_manager": SnowflakePandasIOManager(...)},
        )

        # end_add_downstream_assets


def scope_add_downstream_assets_w_deps():
    from unittest import mock

    with mock.patch("dagster_snowflake.SnowflakeResource"):
        # start_with_deps_add_downstream_assets
        import json
        import dagster as dg

        from dagster_airbyte import load_assets_from_airbyte_instance, AirbyteResource
        from dagster_snowflake import SnowflakeResource

        airbyte_instance = AirbyteResource(
            host="localhost",
            port="8000",
        )

        airbyte_assets = load_assets_from_airbyte_instance(
            airbyte_instance,
        )

        @dg.asset(deps=[dg.AssetKey("stargazers")])
        def stargazers_file(snowflake: SnowflakeResource):
            with snowflake.get_connection() as conn:
                stargazers = conn.cursor.execute(
                    "SELECT * FROM STARGAZERS"
                ).fetch_pandas_all()
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = dg.define_asset_job(
            "my_upstream_job",
            dg.AssetSelection.assets(stargazers_file)
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte dg.asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = dg.Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={"snowflake": SnowflakeResource(...)},
        )

        # end_with_deps_add_downstream_assets


def scope_add_downstream_assets_cloud():
    from unittest import mock

    with mock.patch("dagster_snowflake_pandas.SnowflakePandasIOManager"):
        # start_add_downstream_assets_cloud
        import json
        import dagster as dg

        from dagster_airbyte import (
            build_airbyte_assets,
            AirbyteCloudResource,
        )
        from dagster_snowflake_pandas import SnowflakePandasIOManager
        import pandas as pd

        airbyte_instance = AirbyteCloudResource(
            client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
        )
        airbyte_assets = build_airbyte_assets(
            connection_id="43908042-8399-4a58-82f1-71a45099fff7",
            destination_tables=["releases", "tags", "teams"],
        )

        @dg.asset
        def stargazers_file(stargazers: pd.DataFrame):
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = dg.define_asset_job(
            "my_upstream_job",
            dg.AssetSelection.assets(stargazers_file)
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte dg.asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = dg.Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={
                "snowflake_io_manager": SnowflakePandasIOManager(...),
                "airbyte_instance": airbyte_instance,
            },
        )

        # end_add_downstream_assets_cloud


def scope_add_downstream_assets_cloud_with_deps():
    from unittest import mock

    with mock.patch("dagster_snowflake.SnowflakeResource"):
        # start_with_deps_add_downstream_assets_cloud
        import json
        import dagster as dg

        from dagster_airbyte import (
            build_airbyte_assets,
            AirbyteCloudResource,
        )
        from dagster_snowflake import SnowflakeResource

        airbyte_instance = AirbyteCloudResource(
            client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
        )
        airbyte_assets = build_airbyte_assets(
            connection_id="43908042-8399-4a58-82f1-71a45099fff7",
            destination_tables=["releases", "tags", "teams"],
        )

        @dg.asset(deps=[dg.AssetKey("stargazers")])
        def stargazers_file(snowflake: SnowflakeResource):
            with snowflake.get_connection() as conn:
                stargazers = conn.cursor.execute(
                    "SELECT * FROM STARGAZERS"
                ).fetch_pandas_all()
            with open("stargazers.json", "w", encoding="utf8") as f:
                f.write(json.dumps(stargazers.to_json(), indent=2))

        # only run the airbyte syncs necessary to materialize stargazers_file
        my_upstream_job = dg.define_asset_job(
            "my_upstream_job",
            dg.AssetSelection.assets(stargazers_file)
            .upstream()  # all upstream assets (in this case, just the stargazers Airbyte dg.asset)
            .required_multi_asset_neighbors(),  # all Airbyte assets linked to the same connection
        )

        defs = dg.Definitions(
            jobs=[my_upstream_job],
            assets=[airbyte_assets, stargazers_file],
            resources={
                "snowflake": SnowflakeResource(...),
                "airbyte_instance": airbyte_instance,
            },
        )

        # end_with_deps_add_downstream_assets_cloud


def scope_schedule_assets():
    from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance

    # start_schedule_assets
    airbyte_instance = AirbyteResource(
        host="localhost",
        port="8000",
    )
    airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)

    import dagster as dg

    # materialize all assets
    run_everything_job = dg.define_asset_job("run_everything", selection="*")

    # only run my_airbyte_connection and downstream assets
    my_etl_job = dg.define_asset_job(
        "my_etl_job", dg.AssetSelection.groups("my_airbyte_connection").downstream()
    )

    defs = dg.Definitions(
        assets=[airbyte_assets],
        schedules=[
            dg.ScheduleDefinition(
                job=my_etl_job,
                cron_schedule="@daily",
            ),
            dg.ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ],
    )

    # end_schedule_assets


def scope_schedule_assets_cloud():
    # start_schedule_assets_cloud
    from dagster_airbyte import AirbyteCloudResource, build_airbyte_assets

    import dagster as dg

    airbyte_instance = AirbyteCloudResource(
        client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
        client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
    )
    airbyte_assets = build_airbyte_assets(
        connection_id="43908042-8399-4a58-82f1-71a45099fff7",
        destination_tables=["releases", "tags", "teams"],
    )

    # materialize all assets
    run_everything_job = dg.define_asset_job("run_everything", selection="*")

    defs = dg.Definitions(
        assets=[airbyte_assets],
        schedules=[
            dg.ScheduleDefinition(
                job=run_everything_job,
                cron_schedule="@weekly",
            ),
        ],
        resources={"airbyte": airbyte_instance},
    )

    # end_schedule_assets_cloud
