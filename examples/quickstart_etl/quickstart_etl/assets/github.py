import matplotlib.pyplot as plt
import pandas as pd
from github import Github

from dagster import Field, MetadataValue, StringSource, asset, file_relative_path


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
def github_stars_by_date(context, github_stargazers: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate stars by date.
    """
    df = (
        github_stargazers[["date"]]
        .groupby("date")
        .size()
        .reset_index(name="daily_stars")
        .sort_values(["date"])
    )
    df["total_stars"] = df["daily_stars"].cumsum()

    context.add_output_metadata({"preview": MetadataValue.md(df.tail().to_markdown())})
    return df


@asset(group_name="github", compute_kind="Plot")
def github_star_history(context, github_stars_by_date: pd.DataFrame):
    """
    Line chart of the star history.
    """
    github_stars_by_date.plot(x="date", y="total_stars")
    path = file_relative_path(__file__, "github_star_history.png")
    plt.savefig(path)
    context.add_output_metadata({"plot_path": MetadataValue.path(path)})
