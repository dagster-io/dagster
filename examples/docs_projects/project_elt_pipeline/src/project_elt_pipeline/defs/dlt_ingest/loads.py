import os

import dlt
from dlt.sources.helpers import requests

GITHUB_REPO = os.getenv("GITHUB_REPO", "dagster-io/dagster")


@dlt.resource(write_disposition="merge", primary_key="id")
def issues():
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    owner, name = GITHUB_REPO.split("/")
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{name}/issues",
        headers=headers,
        params={"state": "all", "per_page": 100},
    )
    response.raise_for_status()
    yield [row for row in response.json() if "pull_request" not in row]


@dlt.resource(write_disposition="merge", primary_key="id")
def pull_requests():
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    owner, name = GITHUB_REPO.split("/")
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{name}/pulls",
        headers=headers,
        params={"state": "all", "per_page": 100},
    )
    response.raise_for_status()
    yield response.json()


@dlt.source
def github_data():
    return issues, pull_requests


github_pipeline = dlt.pipeline(
    pipeline_name="github",
    destination="duckdb",
    dataset_name="github_data",
)

github_load_source = github_data()
