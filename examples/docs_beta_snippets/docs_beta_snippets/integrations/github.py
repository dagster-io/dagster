from dagster_github import GithubResource

import dagster as dg


@dg.asset
def github_asset(github: GithubResource):
    github.get_client().create_issue(
        repo_name="dagster",
        repo_owner="dagster-io",
        title="Dagster's first github issue",
        body="this open source thing seems like a pretty good idea",
    )


defs = dg.Definitions(
    assets=[github_asset],
    resources={
        "github": GithubResource(
            github_app_id=dg.EnvVar.int("GITHUB_APP_ID"),
            github_app_private_rsa_key=dg.EnvVar("GITHUB_PRIVATE_KEY"),
            github_installation_id=dg.EnvVar.int("GITHUB_INSTALLATION_ID"),
        )
    },
)
