from pathlib import Path
from typing import Sequence

from dagster import AssetsDefinition, AssetSpec, Definitions, multi_asset
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)


def scrape_website(url: str, result_dir: Path) -> None:
    # This is where you would actually scrape the website
    url_to_file = {
        "https://www.customers-data.com": Path(__file__).parent.parent.parent
        / "data"
        / "customers.csv",
    }
    result_file = url_to_file[url]
    # move result file to result_dir
    result_file.rename(result_dir / result_file.name)


# Each of these would eventually be replaced with a Dagster component.
def build_scraper_asset(specs: Sequence[AssetSpec], url: str) -> AssetsDefinition:
    @multi_asset(specs=specs)
    def run_scraper(context):
        scrape_website(
            url, Path(__file__).parent.parent.parent / "data"
        )

    return run_scraper


raw_customers = build_scraper_asset([AssetSpec(["jaffle_shop", "raw", "raw_customers"])], url="https://www.customers-data.com")

assets = assets_with_task_mappings(
    dag_id="operate_on_customers_data", task_mappings={"scrape_customers_data": [raw_customers]}
)


airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url="http://localhost:8080", username="admin", password="admin"
    ),
    name="airflow_instance",
)

defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance, defs=Definitions(assets=assets)
)
