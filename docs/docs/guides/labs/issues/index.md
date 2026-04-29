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

Issues let you link together multiple failures with a shared root cause, to help you get from noticing a problem to having a fix in production quickly and with full visibility across your team. Issues are designed for an AI-first dev cycle, together with the [Dagster+ AI Assistant](/guides/labs/compass-ai-assistant) and [Dagster skills](/getting-started/ai-tools#about-dagster-skills).

## Creating Issues

Issues can be created from a failed run, from asset or run failure alerts, or from a conversation with the Dagster+ AI Assistant. You can set a summary yourself, or let the Assistant generate one for you.

## Resolving Issues

Issues are optimized for providing context to agents. Invoke the `dagster-expert` skill from an agent session in your codebase to analyze the root cause and develop a solution. For example:

```
/dagster-expert fetch issue 3 and make a plan for resolving the problem
```

## Coming soon

- **Autonomous triage**: The Dagster+ AI Assistant will scan failures and identify shared root causes.
- **Suggested resolutions**: Issues will automatically suggest code changes for you to review and approve.
- **Project tracker integrations**: Integrate directly into your existing workflows through integrations to Github Issues, Linear, JIRA, etc.
