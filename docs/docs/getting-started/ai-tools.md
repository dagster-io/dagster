---
title: AI tools for Dagster
description: Learn how to use Dagster's AI skills to build Dagster projects faster, with best practices built in.
sidebar_label: AI tools
---

Dagster maintains a set of AI skills that give coding agents better context and patterns for building Dagster projects. With these skills installed, your agent can help you create robust data pipelines according to Dagster best practices.

## About Dagster skills

A **skill** is a structured document that your AI coding agent loads when you invoke it. Skills tell agents what to do and how -- for example, which CLI commands to use, how to structure assets, and which patterns to follow.

Dagster maintains two skills in the [dagster-io/skills](https://github.com/dagster-io/skills) repository:

- **`dagster-expert`:** Expert guidance for building production-quality Dagster projects. Covers [`dg`](/api/clis/cli) CLI usage, asset patterns, automation strategies, and implementation workflows.
- **`dignified-python`:** Production-quality Python coding standards for modern Python (types, exceptions, API design). Not Dagster-specific and can be used for general Python quality.

## Installing Dagster skills

<Tabs>
<TabItem value="claude" label="Claude Code">

1. Install and sign in to [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup) using the setup guide.

2. In Claude Code, add the Dagster skills from the plugin marketplace:

   ```text
   /plugin marketplace add dagster-io/skills
   ```

   ![Claude Code plugin marketplace showing the Dagster skills being added](/img/getting-started/ai-tools/claude-marketplace.png)

3. Install the skills you want to use from the plugin. For example, to install the `dagster-expert` skill, run the following command:

   ```text
   /plugin install dagster-expert@dagster-skills
   ```

4. To confirm the skills are enabled, open the plugin list:

   ```text
   /plugin
   ```

   Switch to the **Installed** tab and confirm you see:

   - **dagster-expert**: enabled
   - **dignified-python**: enabled

   If any are disabled, enable them before continuing.

   ![Claude Code plugin list showing dagster-expert and dignified-python enabled](/img/getting-started/ai-tools/claude-plugin.png)

</TabItem>
<TabItem value="cursor" label="Cursor">

:::info Prerequisites

To install Dagster skills with Cursor, you will need `npx`, which comes with Node.js. To install Node.js, see the [official website](https://nodejs.org).

:::

1. Install Cursor from [cursor.com](https://cursor.com) and sign in.

2. Use the `npx` command to install Dagster skills:

   ```bash
   npx skills add dagster-io/skills
   ```

   ![Terminal output showing npx skills install completing successfully](/img/getting-started/ai-tools/npx-install.png)

3. To confirm the skills are enabled, open Cursor's Agent panel. You want at least:

   - `dagster-expert`
   - `dignified-python`

   ![Cursor showing the Dagster skills available in the agent panel](/img/getting-started/ai-tools/cursor-skill.png)

</TabItem>
<TabItem value="copilot" label="GitHub Copilot">

:::info Prerequisites

To install Dagster skills with GitHub Copilot, you will need `npx`, which comes with Node.js. To install Node.js, see the [official website](https://nodejs.org).

:::

1. Install the [GitHub Copilot extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) and the [GitHub Copilot Chat extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) in VS Code, then sign in with your GitHub account.

2. In the Copilot Chat input bar, switch to **Agent** mode using the mode selector (look for the "Ask" / "Edit" dropdown). Without Agent mode, Copilot will suggest commands for you to run manually rather than executing them itself.

3. To add the Dagster skills, run the following command in your terminal:

   ```bash
   npx skills add dagster-io/skills
   ```

   ![Terminal output showing npx skills install completing successfully](/img/getting-started/ai-tools/npx-install.png)

4. In the Copilot Chat panel, verify that the Dagster skills are enabled:

   - `dagster-expert`
   - `dignified-python`

   ![GitHub Copilot Chat showing the Dagster skills available](/img/getting-started/ai-tools/copilot-skill.png)

</TabItem>
<TabItem value="codex" label="Codex">

:::info Prerequisites

To install Dagster skills with Codex, you will need `npx`, which comes with Node.js. To install Node.js, see the [official website](https://nodejs.org).

:::

1. Install [Codex](https://openai.com/codex/) from the official setup guide and sign in.

2. To add the Dagster skills, run the following command in your terminal:

   ```bash
   npx skills add dagster-io/skills
   ```

   ![Terminal output showing npx skills install completing successfully](/img/getting-started/ai-tools/npx-install.png)

3. In Codex settings or the skill list, confirm the Dagster skills are enabled:

   - `dagster-expert`
   - `dignified-python`

   ![Codex showing the Dagster skills enabled](/img/getting-started/ai-tools/codex-skill.png)

</TabItem>
</Tabs>

## Invoking Dagster skills

<Tabs>
<TabItem value="claude" label="Claude Code">

In Claude Code, invoke the skill using the namespaced format:

```text
/dagster-expert create a new Dagster project called my-pipeline
```

</TabItem>
<TabItem value="cursor" label="Cursor">

In Cursor, invoke the skill by name:

```text
/dagster-expert create a new Dagster project called my-pipeline
```

</TabItem>
<TabItem value="copilot" label="GitHub Copilot">

In GitHub Copilot, invoke the skill by name:

```text
/dagster-expert create a new Dagster project called my-pipeline
```

</TabItem>
<TabItem value="codex" label="Codex">

In Codex, invoke the skill by name:

```text
/dagster-expert create a new Dagster project called my-pipeline
```

</TabItem>
</Tabs>

## Next steps

- Follow the [Quickstart](/getting-started/quickstart) to scaffold your first Dagster project
- Learn more in the [AI-Driven Data Engineering](https://courses.dagster.io/) course on Dagster University
