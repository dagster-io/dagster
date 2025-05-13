import dlt
from .github import github_reactions, github_repo_events, github_stargazers


duckdb_repo_reactions_issues_only_source = github_reactions(
    "duckdb", "duckdb", items_per_page=100, max_items=100
).with_resources("issues")
duckdb_repo_reactions_issues_only_pipeline = dlt.pipeline(
    "github_reactions", destination="snowflake", dataset_name="duckdb_issues"
)

airflow_events_source = github_repo_events("apache", "airflow", access_token="")
airflow_events_pipeline = dlt.pipeline(
    "github_events", destination="snowflake", dataset_name="airflow_events"
)

dlthub_dlt_all_data_source = github_reactions("dlt-hub", "dlt")
dlthub_dlt_all_data_pipeline = dlt.pipeline(
    "github_reactions", destination="snowflake", dataset_name="dlthub_reactions"
)

dlthub_dlt_stargazers_source = github_stargazers("dlt-hub", "dlt")
dlthub_dlt_stargazers_pipeline = dlt.pipeline(
    "github_stargazers", destination="snowflake", dataset_name="dlthub_stargazers"
)
