---
title: Issues
sidebar_label: Issues
description: Group failures into Issues to more easily track status and share context with both team members and coding agents
canonicalUrl: '/guides/labs/issues'
slug: '/guides/labs/issues'
sidebar_position: 20
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

Issues let you link together multiple failures with a shared root cause, to help you get from noticing a problem to having a fix in production quickly and with full visibility across your team. Issues are designed for an AI-first dev cycle, together with [Dagster+ AI](/guides/labs/dagster-ai), [Dagster skills](/getting-started/ai-tools#about-dagster-skills), and the [Dagster+ MCP server](/guides/labs/dagster-mcp).

## Creating Issues

Issues are automatically created in the Triage state for you by Dagster+ AI through [proactive monitoring](/guides/labs/dagster-ai/proactive-monitoring). You can also create them directly in several ways:

- **From a failed run** — Open a failed run and create an Issue to track the failure. You can set a summary yourself, or let Dagster+ generate one for you.
- **From alerts** — Alert notifications for failed runs and degraded assets include a link to create an Issue directly from the notification.
- **From a conversation with Dagster+ AI** — During a chat session, create an Issue to track the problem. The AI summary and context are attached automatically. For more information, see [Chat with Dagster+ AI](/guides/labs/dagster-ai/chat).

## Resolving Issues

Issues provide context optimized for coding agents. You can resolve them by:

- **Auto-implement with AI** — Dispatch an AI agent directly from an Issue to create a fix as a GitHub pull request. See [Auto-implement with AI](/guides/labs/dagster-ai/auto-implement).
- **Using the dagster-expert skill** — Invoke the `dagster-expert` skill from an agent session in your codebase to analyze the root cause and develop a solution. For example:

  ```
  /dagster-expert fetch issue 3 and make a plan for resolving the problem
  ```

## Coming soon

- **Issue metadata:** Set an assignee, priority level, or tags on Issues
- **Project tracker integrations:** Integrate directly into your existing workflows through integrations to GitHub Issues, Linear, Jira, etc.
