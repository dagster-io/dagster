---
title: Dagster+ MCP server
description: Connect the Dagster+ MCP server to your AI agent of choice to access information and take actions in your Dagster+ deployment
sidebar_position: 5
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

The Dagster+ MCP server allows you to access information and take actions in your Dagster+ deployment within an AI session.

The server URL depends on the region your organization is in:

| Region | URL                                      |
| ------ | ---------------------------------------- |
| US     | `https://mcp.agent.dagster.cloud/mcp`    |
| EU     | `https://mcp.agent.eu.dagster.cloud/mcp` |

The examples below use the US URL. If your organization is in the EU region, substitute the EU URL.

## Connecting to the MCP server

You can connect to the Dagster+ MCP server using OAuth or by manually specifying a few headers. Using OAuth will use your user permissions when determining the MCP server permissions. If you would like to create a different set of permissions for the MCP server, we recommend creating a [service user](/deployment/dagster-plus/authentication-and-access-control/rbac/users#service-users) and providing authentication headers when adding the MCP server. See the **Other Agent Harnesses** section below for instructions for using headers for authentication.

<Tabs>
<TabItem value="claude" label="Claude Code">

1. Install and sign in to [Claude Code](https://docs.anthropic.com/en/docs/claude-code/setup) using the setup guide.

2. Within your terminal, run the following command:

   ```bash
   claude mcp add --transport http dagster-plus https://mcp.agent.dagster.cloud/mcp
   ```

   EU users should specify the URL `https://mcp.agent.eu.dagster.cloud/mcp`

3. Start a `claude` session and type `/mcp`. Select the `dagster-plus` MCP server and select **Authenticate**. This will
   open a browser window where you can log into Dagster+ and allow the MCP server access to your account.
   ![Claude Code MCP server list showing dagster-plus MCP server](/img/getting-started/ai-tools/claude-mcp.png)

</TabItem>
<TabItem value="codex" label="Codex">

1. Install [Codex](https://openai.com/codex/) from the official setup guide and sign in.

2. Within your terminal, run the following command:

   ```bash
   codex mcp add dagster-plus --url https://mcp.agent.dagster.cloud/mcp
   ```

   EU users should specify the URL `https://mcp.agent.eu.dagster.cloud/mcp`

3. An authentication flow should immediately open and prompt you to allow the MCP server to access your Dagster+ account.

4. Start a `codex` session and type `/mcp`. You should see `dagster-plus` listed as **connected**.

   ![Codex MCP server list showing dagster-plus MCP server](/img/getting-started/ai-tools/codex-mcp.png)

</TabItem>
<TabItem value="other" label="Other Agent Harnesses">

If your agent harness supports OAuth, add the Dagster+ MCP server at `https://mcp.agent.dagster.cloud/mcp` (or `https://mcp.agent.eu.dagster.cloud/mcp` for EU users). Start the OAuth flow for the MCP server according to your provider's instructions.

You can also connect to the Dagster+ MCP server by specifying a URL and a few headers. This bypasses authentication through OAuth.

- **URL:** `https://mcp.agent.dagster.cloud/mcp` (EU: `https://mcp.agent.eu.dagster.cloud/mcp`)

- **Headers:**
  - `Authorization: Bearer [your user token]`
  - `Dagster-Cloud-Organization: [your dagster organization]`

For information on accessing your user token, see [Managing user tokens in Dagster+](/deployment/dagster-plus/management/tokens/user-tokens).

**Example: Adding the Dagster+ MCP server to Claude Code with custom headers**

Within your terminal, run the following command:

```bash
claude mcp add --transport http dagster-plus https://mcp.agent.dagster.cloud/mcp --header "Dagster-Cloud-Organization: [organization]" --header "Authorization: Bearer [token]"
```

</TabItem>
</Tabs>

## Available tools

Using the Dagster+ MCP server you can:

| Object                                   | View | Create/Launch | Update | Delete/Terminate | Insights metrics |
| ---------------------------------------- | :--: | :-----------: | :----: | :--------------: | :--------------: |
| Runs                                     |  ✅  |      ✅       |   ❌   |        ✅        |        ✅        |
| [Run logs](/guides/log-debug/logging)    |  ✅  |      ➖       |   ➖   |        ➖        |        ➖        |
| [Assets](/guides/build/assets)           |  ✅  |      ✅       |   ❌   |        ❌        |        ✅        |
| [Deployments](/deployment)               |  ✅  |      ❌       |   ❌   |        ❌        |        ✅        |
| [Alert policies](/guides/observe/alerts) |  ✅  |      ✅       |   ✅   |        ✅        |        ➖        |
| [Dagster+ Issues](/guides/labs/issues)   |  ✅  |      ✅       |   ✅   |        ✅        |        ➖        |
