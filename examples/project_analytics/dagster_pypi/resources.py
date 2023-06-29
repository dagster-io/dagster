import datetime
import os

import pandas as pd
from dagster import ConfigurableResource, EnvVar
from dagster_dbt import DbtCli
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_gcp_pandas import BigQueryPandasIOManager
from dagster_hex.resources import hex_resource
from google.cloud import bigquery
from pydantic import Field

FILE_PATH = os.path.dirname(__file__)
DBT_PROJECT_DIR = os.path.join(FILE_PATH, "./dbt_project")
DBT_PROFILE_DIR = os.path.join(DBT_PROJECT_DIR, "./profiles")
STEAMPIPE_CONN = os.getenv("STEAMPIPE_CONN")
HEX_API_KEY = os.getenv("HEX_API_KEY")
HEX_PROJECT_ID = os.getenv("HEX_PROJECT_ID")


duckdb_io_manager = DuckDBPandasIOManager(database=os.path.join(DBT_PROJECT_DIR, "dbt_duckdb.db"))

bigquery_pandas_io_manager = BigQueryPandasIOManager(project="westmarindata")


class PyPiResource(ConfigurableResource):
    def get_pypi_download_counts(self, _) -> pd.DataFrame:
        raise NotImplementedError()


class PyPiLocalResource(PyPiResource):
    input_file: str = Field(description="Path to the sample pypi input file")

    def get_pypi_download_counts(self, date) -> pd.DataFrame:
        print("Pretending to fetch for a given date: ", date)
        df = pd.read_csv(self.input_file)
        df["download_date"] = datetime.datetime.strptime(date, "%Y-%m-%d")
        return df


class PyPiBigQueryResource(PyPiResource):
    table: str = Field(description="BigQuery public table to query")

    def get_pypi_download_counts(self, date) -> pd.DataFrame:
        print("Fetching from bigquery for a given date: ", date)
        client = bigquery.Client()
        query = f"""
        SELECT
          date_trunc(file_downloads.timestamp, DAY) AS download_date,
          file_downloads.file.project  AS project_name,
          file_downloads.file.version as project_version,
          COUNT(*) AS file_downloads_count

        FROM `{self.table}` AS file_downloads
        WHERE (file_downloads.file.project LIKE '%dagster%')

        AND date_trunc(file_downloads.timestamp, DAY) = '{date}'
        GROUP BY 1,2,3
        ORDER BY 1,2,3
        """
        return client.query(query).result().to_dataframe()


class GithubResource(ConfigurableResource):
    def get_github_stars(self, _) -> pd.DataFrame:
        raise NotImplementedError()


class GithubLocalResource(GithubResource):
    input_file: str = Field(description="Path to the sample input file")

    def get_github_stars(self, date) -> pd.DataFrame:
        print("Pretending to fetch Github data for a given date: ", date)
        df = pd.read_csv(self.input_file)
        df["date"] = datetime.datetime.strptime(date, "%Y-%m-%d")
        return df


class GithubSteampipeResource(GithubResource):
    streampipe_conn: str = Field(
        description="Steampipe connection string, use steampipe service status to retrieve."
    )

    def get_github_stars(self, date) -> pd.DataFrame:
        print("Fetching Github data from Steampipe for a given date: ", date)
        sql = f"""select
            cast('{date}' as timestamp) as date,
            full_name,
            forks_count,
            stargazers_count,
            subscribers_count,
            watchers_count
        from github_repository
        where full_name in ('dagster-io/dagster')
        """
        df = pd.read_sql(sql, self.streampipe_conn)
        return df


resource_def = {
    "LOCAL": {
        "io_manager": duckdb_io_manager,
        "github": GithubLocalResource(
            input_file=os.path.join(FILE_PATH, "../data/github_star_count.csv")
        ),
        "pypi": PyPiLocalResource(input_file=os.path.join(FILE_PATH, "../data/pypi_downloads.csv")),
        "hex": hex_resource.configured({"api_key": HEX_API_KEY}),
        "dbt": DbtCli(project_dir=DBT_PROJECT_DIR, target="local"),
    },
    "PROD": {
        "io_manager": bigquery_pandas_io_manager,
        "github": GithubSteampipeResource(streampipe_conn=EnvVar("STEAMPIPE_CONN")),
        "pypi": PyPiBigQueryResource(table="bigquery-public-data.pypi.file_downloads"),
        "hex": hex_resource.configured({"api_key": HEX_API_KEY}),
        "dbt": DbtCli(project_dir=DBT_PROJECT_DIR, target="prod"),
    },
}
