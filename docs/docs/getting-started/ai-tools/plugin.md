---
title: Dagster plugin
description: Access all of Dagster's AI tooling with the Dagster plugin
sidebar_position: 10
---

The `dagster` plugin bundles the [`dagster-expert` skill](/getting-started/ai-tools/skills) and the [Dagster+ MCP server](/getting-started/ai-tools/dagster-mcp). The plugin is compatible with Claude Code, Cursor, OpenAI Codex, GitHub Copilot, OpenCode, Pi, and other Agent Skills-compatible tools.

## Installing the Dagster plugin

<Tabs>
<TabItem value="claude" label="Claude Code">

1. Install and sign in to [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup) using the setup guide.

2. In Claude Code, add the Dagster marketplace:

   ```text
   /plugin marketplace add dagster-io/skills
   ```

   ![Claude Code plugin marketplace showing the Dagster marketplace being added](/img/getting-started/ai-tools/claude-marketplace.png)

3. Install the `dagster` plugin:

   ```text
   /plugin install dagster@dagster
   ```

4. To confirm the plugin is installed, open the plugin list:

   ```text
   /plugin
   ```

   Switch to the **Installed** tab and confirm you see **dagster** enabled. If it is disabled, enable it before continuing.

   ![Claude Code plugin list showing dagster enabled](/img/getting-started/ai-tools/claude-plugin.png)

5. (Optional) Authenticate the Dagster+ MCP server by typing `/mcp` and selecting the `dagster-plus` MCP server. Select `Authenticate` and follow the instructions.

   ![Claude Code MCP server list showing dagster-plus MCP server](/img/getting-started/ai-tools/claude-mcp.png)

   :::info For EU users

   Users with Dagster+ organizations in the EU region need to set an environment variable to configure the MCP server.

   ```text
   export DAGSTER_CLOUD_MCP_URL=https://mcp.agent.eu.dagster.cloud/mcp
   ```

   Then follow the authentication instructions in your Claude Code session.

   :::

</TabItem>
<TabItem value="cursor" label="Cursor">

The Dagster plugin can be installed from the official Cursor marketplace:

1. Install Cursor from [cursor.com](https://cursor.com) and sign in.

2. Open the [Customize](https://cursor.com/docs/customize-cursor) page in Cursor.

3. Search for `Dagster`, then click `Add` to add the `Dagster` plugin.

   ![Cursor plugin marketplace showing the Dagster plugin being added](/img/getting-started/ai-tools/cursor-marketplace.png)

</TabItem>

<TabItem value="codex" label="Codex">

1. Install [Codex](https://openai.com/codex/) from the official setup guide and sign in.

2. In your terminal, add the `dagster` marketplace to Codex:

   ```text
   codex plugin marketplace add dagster-io/skills --ref release-stable
   ```

3. Install the `dagster` plugin:

   ```text
   codex plugin add dagster@dagster
   ```

4. In Codex settings or the skill list, confirm the `dagster-expert` skill is enabled.

   ![Codex showing the dagster skill enabled](/img/getting-started/ai-tools/codex-skill.png)

</TabItem>

<TabItem value="copilot" label="GitHub Copilot">

1. Install the [GitHub Copilot extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) and the [GitHub Copilot Chat extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) in VS Code, then sign in with your GitHub account.

2. Install the [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli).

3. To add the Dagster plugin, run the following command in your terminal:

   ```text
   copilot plugin install dagster-io/skills:plugins/dagster
   ```

4. In the Copilot Chat panel, verify that the `dagster-expert` skill is enabled.

   ![GitHub Copilot Chat showing the dagster-expert skill available](/img/getting-started/ai-tools/copilot-skill.png)

</TabItem>
</Tabs>

:::warning

The `dagster-expert` skill was previously published as part of a plugin called `dagster-expert`. As of September 14, 2026, the `dagster-expert` plugin is deprecated and the `dagster-expert` skill is published as part of the `dagster` plugin. The `dagster-expert` skill itself is unchanged and is still invoked with `/dagster-expert`.

The `dagster-expert` plugin remains installable to prevent sudden breakages, but has been replaced with a stub skill that carries no guidance and points to instructions to migrate to the `dagster` plugin. To migrate, uninstall the `dagster-expert` plugin and follow the installation instructions for the `dagster` plugin.

:::
