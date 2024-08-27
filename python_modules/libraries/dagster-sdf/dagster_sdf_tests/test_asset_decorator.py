from pathlib import Path

from dagster import AssetExecutionContext, AssetKey, materialize
from dagster_sdf.asset_decorator import sdf_assets
from dagster_sdf.asset_utils import get_asset_key_for_table_id
from dagster_sdf.dagster_sdf_translator import DagsterSdfTranslator, DagsterSdfTranslatorSettings
from dagster_sdf.resource import SdfCliResource
from dagster_sdf.sdf_workspace import SdfWorkspace

from dagster_sdf_tests.sdf_workspaces import lineage_upstream_path, moms_flower_shop_path


def test_asset_deps(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        )
    )
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.asset_deps == {
        AssetKey(["moms_flower_shop", "raw", "raw_addresses"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_customers"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_inapp_events"]): set(),
        AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]): set(),
        AssetKey(["moms_flower_shop", "staging", "app_installs"]): {
            AssetKey(["moms_flower_shop", "staging", "inapp_events"]),
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]),
        },
        AssetKey(["moms_flower_shop", "staging", "app_installs_v2"]): {
            AssetKey(["moms_flower_shop", "staging", "inapp_events"]),
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"]),
        },
        AssetKey(["moms_flower_shop", "staging", "customers"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_addresses"]),
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"]),
            AssetKey(["moms_flower_shop", "raw", "raw_customers"]),
        },
        AssetKey(["moms_flower_shop", "staging", "inapp_events"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_inapp_events"])
        },
        AssetKey(["moms_flower_shop", "staging", "marketing_campaigns"]): {
            AssetKey(["moms_flower_shop", "raw", "raw_marketing_campaign_events"])
        },
        AssetKey(["moms_flower_shop", "staging", "stg_installs_per_campaign"]): {
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"])
        },
        AssetKey(["moms_flower_shop", "analytics", "agg_installs_and_campaigns"]): {
            AssetKey(["moms_flower_shop", "staging", "app_installs_v2"])
        },
        AssetKey(["moms_flower_shop", "analytics", "dim_marketing_campaigns"]): {
            AssetKey(["moms_flower_shop", "staging", "marketing_campaigns"]),
            AssetKey(["moms_flower_shop", "staging", "stg_installs_per_campaign"]),
        },
    }

    asset_key = get_asset_key_for_table_id(
        [my_flower_shop_assets], "moms_flower_shop.raw.raw_addresses"
    )
    assert asset_key == AssetKey(["moms_flower_shop", "raw", "raw_addresses"])


def test_upstream_deps(lineage_upstream_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=lineage_upstream_path, target_dir=lineage_upstream_target_dir
        )
    )
    def my_lineage_upstream_assets(): ...

    assert my_lineage_upstream_assets.asset_deps == {
        AssetKey(["lineage", "pub", "depend_on_upstream"]): {
            AssetKey(["build_upstream_depend_on"])
        },
        AssetKey(["lineage", "pub", "knis"]): {AssetKey(["lineage", "pub", "middle"])},
        AssetKey(["lineage", "pub", "middle"]): {AssetKey(["build_upstream_source"])},
        AssetKey(["lineage", "pub", "sink"]): {AssetKey(["lineage", "pub", "middle"])},
    }

    asset_key = get_asset_key_for_table_id(
        [my_lineage_upstream_assets], "lineage.pub.depend_on_upstream"
    )
    assert asset_key == AssetKey(["lineage", "pub", "depend_on_upstream"])


def test_sdf_with_materialize(moms_flower_shop_target_dir: Path) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        )
    )
    def my_sdf_assets(context: AssetExecutionContext, sdf: SdfCliResource):
        yield from sdf.cli(
            ["run", "--save", "info-schema"],
            target_dir=moms_flower_shop_target_dir,
            context=context,
        ).stream()

    first_result = materialize(
        [my_sdf_assets],
        resources={"sdf": SdfCliResource(workspace_dir=moms_flower_shop_path)},
    )

    assert first_result.success
    first_num_asset_materialization_events = len(first_result.get_asset_materialization_events())
    assert first_num_asset_materialization_events > 0

    cached_result = materialize(
        [my_sdf_assets],
        resources={"sdf": SdfCliResource(workspace_dir=moms_flower_shop_path)},
    )

    assert cached_result.success
    materialization_events = cached_result.get_asset_materialization_events()
    assert not any(
        [
            not event.materialization.metadata["Materialized From Cache"]
            for event in materialization_events
        ]
    )
    cached_num_asset_materialization_events = len(cached_result.get_asset_materialization_events())
    assert first_num_asset_materialization_events == cached_num_asset_materialization_events


def test_with_custom_translater_asset_key_fn(moms_flower_shop_target_dir: Path) -> None:
    class CustomDagsterSdfTranslator(DagsterSdfTranslator):
        def get_asset_key(self, catalog: str, schema: str, table_name: str) -> AssetKey:
            return AssetKey([f"pre-{catalog}-suff", f"pre-{schema}-suff", f"pre-{table_name}-suff"])

    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path, target_dir=moms_flower_shop_target_dir
        ),
        dagster_sdf_translator=CustomDagsterSdfTranslator(),
    )
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.asset_deps == {
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_addresses-suff"]): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_customers-suff"]): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_inapp_events-suff"]): set(),
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_marketing_campaign_events-suff"]
        ): set(),
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            ),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            ),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-customers-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_addresses-suff"]),
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"]),
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_customers-suff"]),
        },
        AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-inapp_events-suff"]): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_inapp_events-suff"])
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-marketing_campaigns-suff"]
        ): {
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-raw-suff",
                    "pre-raw_marketing_campaign_events-suff",
                ]
            )
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-stg_installs_per_campaign-suff"]
        ): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"])
        },
        AssetKey(
            [
                "pre-moms_flower_shop-suff",
                "pre-analytics-suff",
                "pre-agg_installs_and_campaigns-suff",
            ]
        ): {
            AssetKey(["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-app_installs_v2-suff"])
        },
        AssetKey(
            ["pre-moms_flower_shop-suff", "pre-analytics-suff", "pre-dim_marketing_campaigns-suff"]
        ): {
            AssetKey(
                ["pre-moms_flower_shop-suff", "pre-staging-suff", "pre-marketing_campaigns-suff"]
            ),
            AssetKey(
                [
                    "pre-moms_flower_shop-suff",
                    "pre-staging-suff",
                    "pre-stg_installs_per_campaign-suff",
                ]
            ),
        },
    }

    asset_key = get_asset_key_for_table_id(
        [my_flower_shop_assets], "pre-moms_flower_shop-suff.pre-raw-suff.pre-raw_addresses-suff"
    )
    assert asset_key == AssetKey(
        ["pre-moms_flower_shop-suff", "pre-raw-suff", "pre-raw_addresses-suff"]
    )


def test_asset_descriptions(moms_flower_shop_target_dir: str) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_raw_sql_description=False)
        ),
    )
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.descriptions_by_key == {
        AssetKey(
            ["moms_flower_shop", "analytics", "agg_installs_and_campaigns"]
        ): "sdf view moms_flower_shop.analytics.agg_installs_and_campaigns",
        AssetKey(
            ["moms_flower_shop", "staging", "inapp_events"]
        ): "sdf view moms_flower_shop.staging.inapp_events",
        AssetKey(
            ["moms_flower_shop", "analytics", "dim_marketing_campaigns"]
        ): "sdf view moms_flower_shop.analytics.dim_marketing_campaigns",
        AssetKey(
            ["moms_flower_shop", "staging", "app_installs"]
        ): "This table is a staging table which adds campaign information to app install events\n",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_addresses"]
        ): "All relevant information related to street addresses known to mom's flower shop.  This information comes from the user input into the mobile app.\n",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_marketing_campaign_events"]
        ): "An hourly table logging marketing campaigns. If a campaign is running that hour, it will be logged in the table.  If no campaigns are running for a certain houe, no campaigns will be logged.\n",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_inapp_events"]
        ): "Logged actions (events) that users perform inside the mobile app of mom's flower shop.",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_customers"]
        ): "All relevant information related to customers known to mom's flower shop.  This information comes from the user input into the mobile app.\n",
        AssetKey(
            ["moms_flower_shop", "staging", "app_installs_v2"]
        ): "sdf view moms_flower_shop.staging.app_installs_v2",
        AssetKey(
            ["moms_flower_shop", "staging", "stg_installs_per_campaign"]
        ): "sdf view moms_flower_shop.staging.stg_installs_per_campaign",
        AssetKey(
            ["moms_flower_shop", "staging", "marketing_campaigns"]
        ): "sdf view moms_flower_shop.staging.marketing_campaigns",
        AssetKey(
            ["moms_flower_shop", "staging", "customers"]
        ): "sdf view moms_flower_shop.staging.customers",
    }


def test_asset_descriptions_with_raw_sql(moms_flower_shop_target_dir: str) -> None:
    @sdf_assets(
        workspace=SdfWorkspace(
            workspace_dir=moms_flower_shop_path,
            target_dir=moms_flower_shop_target_dir,
        ),
        dagster_sdf_translator=DagsterSdfTranslator(
            settings=DagsterSdfTranslatorSettings(enable_raw_sql_description=True)
        ),
    )
    def my_flower_shop_assets(): ...

    assert my_flower_shop_assets.descriptions_by_key == {
        AssetKey(
            ["moms_flower_shop", "analytics", "agg_installs_and_campaigns"]
        ): "sdf view moms_flower_shop.analytics.agg_installs_and_campaigns\n\n#### Raw SQL:\n```\n    SELECT \n        -- install events data\n        DATE_FORMAT(install_time, '%Y-%m-%d') AS install_date,\n        campaign_name,\n        platform,\n        COUNT(DISTINCT customer_id) AS distinct_installs\n    FROM staging.app_installs_v2\n    GROUP BY 1,2,3\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "app_installs"]
        ): "This table is a staging table which adds campaign information to app install events\n\n\n#### Raw SQL:\n```\n    SELECT \n        -- install events data\n        COALESCE(m.event_id, i.event_id) AS event_id,\n        i.customer_id,\n        i.event_time AS install_time,\n        i.platform,\n\n        -- marketing campaigns data - if doesn't exist than organic\n        COALESCE(m.campaign_id, -1) AS campaign_id, \n        COALESCE(m.campaign_name, 'organic') AS campaign_name,\n        COALESCE(m.c_name, 'organic') AS campaign_type\n    FROM inapp_events i \n        LEFT OUTER JOIN raw.raw_marketing_campaign_events m\n            ON (i.event_id = m.event_id) \n    WHERE event_name = 'install'\n```",
        AssetKey(
            ["moms_flower_shop", "analytics", "dim_marketing_campaigns"]
        ): "sdf view moms_flower_shop.analytics.dim_marketing_campaigns\n\n#### Raw SQL:\n```\n    SELECT \n        -- marketing campaigns dimensions\n        m.campaign_id,\n        m.campaign_name,\n        -- metrics\n        i.total_num_installs,\n        total_campaign_spent / \n            NULLIF(i.total_num_installs, 0) AS avg_customer_acquisition_cost,\n        campaign_duration / \n            NULLIF(i.total_num_installs, 0) AS install_duration_ratio\n    FROM staging.marketing_campaigns m\n        LEFT OUTER JOIN staging.stg_installs_per_campaign i\n        ON (m.campaign_id = i.campaign_id)\n    ORDER BY total_num_installs DESC NULLS LAST\n```",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_marketing_campaign_events"]
        ): "An hourly table logging marketing campaigns. If a campaign is running that hour, it will be logged in the table.  If no campaigns are running for a certain houe, no campaigns will be logged.\n\n\n#### Raw SQL:\n```\n    CREATE TABLE raw_marketing_campaign_events \n    WITH (FORMAT='PARQUET', LOCATION='seeds/parquet/marketing_campaign_events.parquet');\n```",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_customers"]
        ): "All relevant information related to customers known to mom's flower shop.  This information comes from the user input into the mobile app.\n\n\n#### Raw SQL:\n```\n    CREATE TABLE raw_customers \n    WITH (FORMAT='PARQUET', LOCATION='seeds/parquet/customers.parquet');\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "inapp_events"]
        ): "sdf view moms_flower_shop.staging.inapp_events\n\n#### Raw SQL:\n```\n    SELECT \n        event_id,\n        customer_id,\n        FROM_UNIXTIME(event_time/1000) AS event_time,  \n        event_name,\n        event_value,\n        additional_details,\n        platform,\n        campaign_id\n    FROM raw.raw_inapp_events\n```",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_addresses"]
        ): "All relevant information related to street addresses known to mom's flower shop.  This information comes from the user input into the mobile app.\n\n\n#### Raw SQL:\n```\n    CREATE TABLE raw_addresses \n    WITH (FORMAT='PARQUET', LOCATION='seeds/parquet/addresses.parquet');\n```",
        AssetKey(
            ["moms_flower_shop", "raw", "raw_inapp_events"]
        ): "Logged actions (events) that users perform inside the mobile app of mom's flower shop.\n\n#### Raw SQL:\n```\n    CREATE TABLE raw_inapp_events \n    WITH (FORMAT='PARQUET', LOCATION='seeds/parquet/inapp_events.parquet');\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "customers"]
        ): "sdf view moms_flower_shop.staging.customers\n\n#### Raw SQL:\n```\n    SELECT \n        c.id AS customer_id,\n        c.first_name,\n        c.last_name,\n        c.first_name || ' ' || c.last_name AS full_name,\n        c.email,\n        c.gender,\n    \n        -- Marketing info\n        i.campaign_id,\n        i.campaign_name,\n        i.campaign_type,\n\n        -- Address info\n        c.address_id,\n        a.full_address,\n        a.state\n    FROM raw.raw_customers c \n\n        LEFT OUTER JOIN app_installs_v2 i\n            ON (c.id = i.customer_id)\n\n        LEFT OUTER JOIN raw.raw_addresses a\n            ON (c.address_id = a.address_id)\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "app_installs_v2"]
        ): "sdf view moms_flower_shop.staging.app_installs_v2\n\n#### Raw SQL:\n```\n    SELECT \n        DISTINCT\n        -- install events data\n        i.event_id,\n        i.customer_id,\n        i.event_time AS install_time,\n        i.platform,\n\n        -- marketing campaigns data - if doesn't exist than organic\n        COALESCE(m.campaign_id, -1) AS campaign_id, \n        COALESCE(m.campaign_name, 'organic') AS campaign_name,\n        COALESCE(m.c_name, 'organic') AS campaign_type\n    FROM inapp_events i \n        LEFT OUTER JOIN raw.raw_marketing_campaign_events m\n            ON (i.campaign_id = m.campaign_id) \n    WHERE event_name = 'install'\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "stg_installs_per_campaign"]
        ): "sdf view moms_flower_shop.staging.stg_installs_per_campaign\n\n#### Raw SQL:\n```\n    SELECT \n        campaign_id,\n        COUNT(event_id) AS total_num_installs\n    FROM app_installs_v2\n    GROUP BY 1\n```",
        AssetKey(
            ["moms_flower_shop", "staging", "marketing_campaigns"]
        ): "sdf view moms_flower_shop.staging.marketing_campaigns\n\n#### Raw SQL:\n```\n    SELECT \n        campaign_id,\n        campaign_name,\n        SUBSTR(c_name, 1, LENGTH(c_name)-1) AS campaign_type,\n        MIN(\n            FROM_UNIXTIME(event_time/1000) -- convert unixtime from milliseconds to seconds\n        ) AS start_time,\n        MAX(\n            FROM_UNIXTIME(event_time/1000) -- convert unixtime from milliseconds to seconds\n        ) AS end_time,\n        COUNT(event_time) AS campaign_duration,\n        SUM(cost) AS total_campaign_spent,\n        ARRAY_AGG(event_id) AS event_ids\n    FROM raw.raw_marketing_campaign_events\n    GROUP BY \n        campaign_id,\n        campaign_name,\n        campaign_type\n```",
    }
