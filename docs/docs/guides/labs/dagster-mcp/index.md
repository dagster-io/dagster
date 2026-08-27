---
title: Dagster+ MCP server
description: Connect the Dagster+ MCP server to your AI agent of choice to access information and take actions in your Dagster+ deployment
canonicalUrl: '/guides/labs/dagster-mcp'
slug: '/guides/labs/dagster-mcp'
sidebar_position: 5
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

The Dagster+ MCP server allows you to access information and take actions in your Dagster+ deployment within an AI session.

The server URL depends on the region your organization is in:

| Region | URL                                      |
| ------ | ---------------------------------------- |
| US     | `https://mcp.agent.dagster.cloud/mcp`    |
| EU     | `https://mcp.agent.eu.dagster.cloud/mcp` |

The examples below use the US URL. If your organization is in the EU region, substitute the EU URL.

## Connecting to the MCP server

You can connect to the Dagster+ MCP server using OAuth or by manually specifying a few headers. Using OAuth will use your user permissions when determining the MCP server permissions. If you would like to create a different set of permissions for the MCP server, we recommend creating a [service user](/deployment/dagster-plus/authentication-and-access-control/rbac/users#service-users) and providing authentication headers when adding the MCP server.

<Tabs>
<TabItem value="oauth" label="OAuth">
Add the Dagster+ MCP server to your client by specifying the following URL:

- **URL:** `https://mcp.agent.dagster.cloud/mcp` (EU: `https://mcp.agent.eu.dagster.cloud/mcp`)

Then authenticate the MCP server according to the client instructions.

**Example: Adding the Dagster+ MCP server to Claude Code**

Within your terminal, run the following command:

```bash
claude mcp add --transport http dagster-plus https://mcp.agent.dagster.cloud/mcp
```

Then start a `claude` session and type `/mcp`. Select the `dagster-plus` MCP server and select `Authenticate`. This will
open a browser window where you can log into Dagster+ and allow the MCP server access to your account.

</TabItem>
<TabItem value="headers" label="Manually provide headers">
Connect to the Dagster+ MCP server by specifying a URL and a few headers.

- **URL:** `https://mcp.agent.dagster.cloud/mcp` (EU: `https://mcp.agent.eu.dagster.cloud/mcp`)

- **Headers:**
  - `Authorization: Bearer [your user token]`
  - `Dagster-Cloud-Organization: [your dagster organization]`

For information on accessing your user token, see [Managing user tokens in Dagster+](/deployment/dagster-plus/management/tokens/user-tokens).

**Example: Adding the Dagster+ MCP server to Claude Code**

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
