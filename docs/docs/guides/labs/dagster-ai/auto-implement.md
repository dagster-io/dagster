---
title: 'Auto-implement'
description: 'Dispatch an AI coding agent from any Issue to create a fix as a GitHub pull request'
sidebar_label: 'Auto-implement'
sidebar_position: 30
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

From any [Issue](/guides/labs/issues), you can dispatch an AI coding agent to plan and implement a fix via GitHub Actions and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Prerequisites

- A Dagster+ organization with [Dagster+ AI](/guides/labs/dagster-ai) enabled
- A GitHub App installation connected to your organization
- The `dg` CLI installed (`pip install dagster-dg`)
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

### Step 1: Scaffold the GitHub workflow

Run the following command in your repository to generate the GitHub Actions workflow:

```bash
dg labs scaffold github-actions-ai-dispatch
```

This creates `.github/workflows/dg-ai-dispatch.yml`. Commit and push the file to your repository's default branch.

### Step 2: Add the Anthropic API key

Add `ANTHROPIC_API_KEY` as a [GitHub Actions repository secret](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions).

## Dispatching from the UI

1. Navigate to an Issue in the Dagster+ UI.
2. Select the GitHub repository that contains the code to fix.
3. The system checks for the required workflow file in the selected repository.
4. Click **Implement with Dagster+ AI**.

{/* ![Dispatch repository selection](/images/guides/labs/dagster-ai/dispatch-repo-select.png) */}

After dispatching, links to the draft PR and workflow run appear in the UI.

{/* ![Dispatch success](/images/guides/labs/dagster-ai/dispatch-success.png) */}

## Dispatching from the CLI

```bash
dg labs ai dispatch <issue_id>
```

The CLI infers the target repository from the `origin` git remote. To target a different repository, pass `--repo owner/repo`.

Required configuration (via flags or environment variables):

| Flag             | Environment variable         | Description                         |
| ---------------- | ---------------------------- | ----------------------------------- |
| `--organization` | `DAGSTER_CLOUD_ORGANIZATION` | Your Dagster+ organization name     |
| `--deployment`   | `DAGSTER_CLOUD_DEPLOYMENT`   | The deployment containing the Issue |
| `--api-token`    | `DAGSTER_CLOUD_API_TOKEN`    | A Dagster+ API token                |

## Customizing the workflow

The scaffolded workflow at `.github/workflows/dg-ai-dispatch.yml` can be customized:

- **Timeouts:** Adjust `timeout-minutes` on the `plan` or `implement` jobs.
- **Model:** Change the `default` value of the `model_name` input.
- **Setup steps:** Add steps before the Claude Code action (e.g., installing dependencies, setting up a Python environment).
- **Prompts:** Modify the `prompt` field in each Claude Code action step to customize how the agent approaches your codebase.

## Coming soon

- **Support for other models and runtimes:** You will be able to launch auto-implement with alternative providers other than GitHub Actions and Claude Code.
