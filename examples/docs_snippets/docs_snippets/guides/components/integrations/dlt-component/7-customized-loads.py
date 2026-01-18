import dlt
from .github import github_reactions, github_repo_events, github_stargazers

dlthub_dlt_stargazers_source = github_stargazers("dlt-hub", "dlt")
dlthub_dlt_stargazers_pipeline = dlt.pipeline(
    "github_stargazers", destination="snowflake", dataset_name="dlthub_stargazers"
)
