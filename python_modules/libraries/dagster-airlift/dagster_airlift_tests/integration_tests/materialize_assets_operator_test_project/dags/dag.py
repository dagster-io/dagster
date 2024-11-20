import logging
import os
from datetime import datetime

import requests
from airflow import DAG
from airflow.utils.context import Context
from dagster_airlift.in_airflow.materialize_assets_operator import BaseMaterializeAssetsOperator

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.INFO)
requests_log.propagate = True


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

dag = DAG(
    "the_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
    start_date=datetime(2023, 1, 1),
)


class BlankSessionAssetsOperator(BaseMaterializeAssetsOperator):
    """An assets operator which opens a blank session and expects the dagster URL to be set in the environment.
    The dagster url is expected to be set in the environment as DAGSTER_URL.
    """

    def get_dagster_session(self, context: Context) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self, context: Context) -> str:
        return os.environ["DAGSTER_URL"]


the_task = BlankSessionAssetsOperator(
    # Test both string syntax and list of strings syntax.
    task_id="some_task",
    dag=dag,
    asset_key_paths=["some_asset", ["other_asset"], ["nested", "asset"]],
)
