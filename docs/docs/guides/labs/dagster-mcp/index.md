---
title: Dagster+ MCP
sidebar_label: Dagster+ MCP
description: Connect the Dagster+ MCP server to your AI agent of choice to access information and take actions in your Dagster+ deployment
canonicalUrl: '/guides/labs/dagster-mcp'
slug: '/guides/labs/dagster-mcp'
sidebar_position: 5
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

The Dagster+ MCP server allows you to access information and take actions in your Dagster+ deployment within an AI session.

## Connecting to the MCP server

Connect to the Dagster+ MCP server by specifying a URL and a few headers.

- **URL:** `https://mcp.agent.dagster.cloud/mcp`

- **Headers:**
  - `Authorization: Bearer [your user token]`
  - `Dagster-Cloud-Organization: [your dagster organization]`

For information on accessing your user token, see [Managing user tokens in Dagster+](/deployment/dagster-plus/management/tokens/user-tokens).
If you would like to create a new token with a different set of permissions, we recommend creating a [service user](/deployment/dagster-plus/authentication-and-access-control/rbac/users#service-users).

### Example: Adding the Dagster+ MCP server to Claude Code

Within your terminal, run the following command:

```bash
claude mcp add --transport http dagster-plus https://mcp.agent.dagster.cloud/mcp --header "Dagster-Cloud-Organization: [organization]" --header "Authorization: Bearer [token]"
```

## Available tools

Using the Dagster+ MCP server you can:

| Object                                   | View | Create/Launch | Update | Delete/Terminate | Insights metrics |
| ---------------------------------------- | :--: | :-----------: | :----: | :--------------: | :--------------: |
| Runs                                     |  ✅  |      ✅       |   ❌   |        ✅        |        ✅        |
| [Run logs](/guides/log-debug/logging)    |  ✅  |      ➖       |   ➖   |        ➖        |        ➖        |
| [Assets](/guides/build/assets)           |  ✅  |      ❌       |   ❌   |        ❌        |        ✅        |
| [Deployments](/deployment)               |  ✅  |      ❌       |   ❌   |        ❌        |        ✅        |
| [Alert policies](/guides/observe/alerts) |  ✅  |      ✅       |   ✅   |        ✅        |        ➖        |
| [Dagster+ Issues](/guides/labs/issues)   |  ✅  |      ✅       |   ✅   |        ✅        |        ➖        |

## Coming soon

- **Dynamic Client Registration (DCR) support:** Authenticate with Dagster+ using OAuth rather than a user token.
