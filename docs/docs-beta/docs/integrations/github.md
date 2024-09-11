---
layout: Integration
status: published
name: GitHub
title: Dagster & GitHub
sidebar_label: GitHub
excerpt: Integrate with GitHub Apps and automate operations within your github repositories.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-github
docslink: 
partnerlink: https://github.com/
logo: /integrations/Github.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

This library provides an integration with _[GitHub Apps](https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps)_ by providing a thin wrapper on the GitHub v4 GraphQL API. This allows for automating operations within your GitHub repositories and with the tighter permissions scopes that GitHub Apps allow for vs using a personal token.

### Installation

```bash
pip install dagster-github
```

### Example

```python
import dagster as dg
from dagster_github import GithubResource


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
            github_app_id=dg.EnvVar("GITHUB_APP_ID"),
            github_app_private_rsa_key=dg.EnvVar("GITHUB_PRIVATE_KEY"),
            github_installation_id=dg.EnvVar("GITHUB_INSTALLATION_ID"),
        )
    },
)
```

### About GitHub

**GitHub** provides a highly available git repo, access control, bug tracking, software feature requests, task management, continuous integration, and wikis for open source and commercial projects.
