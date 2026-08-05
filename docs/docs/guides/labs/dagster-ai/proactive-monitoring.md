---
title: 'Proactive monitoring'
description: 'Dagster+ AI scans your deployments for failure patterns and creates Issues to surface problems automatically'
sidebar_label: 'Proactive monitoring'
sidebar_position: 20
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

Dagster+ AI scans your deployments for failure patterns and creates Issues to summarize problems, identify root causes, and suggest solutions for you to review. For more information, see [Issues](/guides/labs/issues).

## Reviewing auto-created Issues

Issues appear in the **Triage** section of the [Issues list](/guides/labs/issues). Review each Issue and either promote it to **Open** to track actively, or set it to **Canceled** to dismiss.

{/* ![Issues list with triage status](/images/guides/labs/dagster-ai/issues-list-triage.png) */}

## Resolving Issues

Once you've reviewed an Issue, you can resolve it by:

- Dispatch an AI agent to create a fix as a pull request. For more information, see [Auto-implement with AI](/guides/labs/dagster-ai/auto-implement).
- Invoke the `dagster-expert` skill from an agent session in your codebase to analyze the root cause and develop a solution. For more information, see the [dagster-expert skill](/getting-started/ai-tools).

## Coming soon

- **Custom prompts:** Guide the AI agent's analysis and triage decisions with context specific to your team
- **Automated actions:** Configure the AI agent to take additional actions beyond triage, such as preparing a fix through auto-implement or retrying a run
- **Issue metadata rules:** Set priority, assignees, or other metadata on automatically created Issues
- **Issue notifications:** Receive alerts about newly created Issues
