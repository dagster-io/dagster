import pandas as pd
import pandas_gbq
from github import Github

from dagster import Field, MetadataValue, StringSource, asset, OutputContext


# (dataset, exists_ok) = [context.op_config.get(k) for k in ("dataset", "exists_ok")]
# context.log.info("executing BQ create_dataset for dataset %s" % (dataset))
# context.resources.bigquery.create_dataset(dataset, exists_ok)

from dagster import IOManager, io_manager


class BigQueryPandasIOManager(IOManager):
    # def _get_path(self, context) -> str:
    #     return "/".join(context.asset_key.path)

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        table_id = ""
        project_id = ""
        pandas_gbq.to_gbq(obj, table_id, project_id=project_id)
        # write_csv(self._get_path(context), obj)

    def load_input(self, context) -> pd.DataFrame:
        import pandas

        sql = """
            SELECT name
            FROM `bigquery-public-data.usa_names.usa_1910_current`
            WHERE state = 'TX'
            LIMIT 100
        """

        # Run a Standard SQL query using the environment's default project
        df = pandas.read_gbq(sql, dialect="standard")

        # Run a Standard SQL query with the project set explicitly
        project_id = "your-project-id"
        df = pandas.read_gbq(sql, project_id=project_id, dialect="standard")

        return read_csv(self._get_path(context))


@io_manager(required_resource_keys={"bigquery"})
def bigquery_pandas_io_manager(init_context):
    return BigQueryPandasIOManager()


@asset(
    group_name="github",
    config_schema={
        "github_token": Field(StringSource, default_value={"env": "MY_GITHUB_TOKEN"}),
        "repo": Field(str, default_value="dagster-io/dagster"),
    },
    compute_kind="GitHub API",
)
def github_stargazers(context) -> pd.DataFrame:
    """
    Get github stargazers from GitHub API.
    Docs: https://pygithub.readthedocs.io/en/latest/github_objects/Stargazer.html

    **GitHub token is required.** TODO: add github token + secret/envvar doc link
    """
    github_token = context.op_config["github_token"]
    repo = context.op_config["repo"]

    github = Github(github_token)
    result = list(github.get_repo(repo).get_stargazers_with_dates())

    df = pd.DataFrame(
        [
            {
                "stargazer": stargazer.user.login,
                "date": stargazer.starred_at.date(),
            }
            for stargazer in result
        ]
    )
    df["date"] = pd.to_datetime(df["date"]).dt.date

    context.add_output_metadata({"preview": MetadataValue.md(df.head().to_markdown())})
    return df


@asset(group_name="github", compute_kind="Pandas")
def github_stars_by_date(context, github_stargazers):
    """
    Aggregate stars by date.
    """
    df = (
        github_stargazers[["date"]]
        .groupby("date")
        .size()
        .reset_index(name="count")
        .sort_values(["count"], ascending=False)
    )

    df["total_github_stars"] = df["stargazer"].cumsum()

    context.add_output_metadata({"preview": MetadataValue.md(df.head().to_markdown())})
    return df
