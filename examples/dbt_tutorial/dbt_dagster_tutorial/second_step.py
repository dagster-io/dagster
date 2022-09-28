import os
import pandas as pd
import plotly.express as px
import plotly.offline as po

from dagster_dbt import load_assets_from_dbt_project, dbt_cli_resource
from dagster import repository, with_resources, asset, AssetIn, fs_io_manager, Output, MetadataValue
from dagster._utils import file_relative_path

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


DBT_PROJECT_PATH=file_relative_path(__file__, "../jaffle_shop")
DBT_PROFILES=os.path.expanduser('~') + "/.dbt"

dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["jamie"])

@asset(
    group_name="staging",
    io_manager_key="fs_io_manager",
    key_prefix="jamie"
)
def order_count_chart(customers: pd.DataFrame):
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    plot_html = po.plot(fig)

    return plot_html


@repository
def jaffle_shop_repository():
    return with_resources(
            [*dbt_assets, order_count_chart],
            {
                "dbt": dbt_cli_resource.configured(
                    {"project_dir": DBT_PROJECT_PATH},
                ),
                "io_manager": snowflake_io_manager.configured(
                    {
                        "account": "na94824.us-east-1",
                        "user": "jamie@elementl.com",
                        "password": {
                            "env": "SNOWFLAKE_PASSWORD"
                        },
                        "database": "SANDBOX",
                        "warehouse": "ELEMENTL",
                    }
                ),
                "fs_io_manager": fs_io_manager,
            },
        )