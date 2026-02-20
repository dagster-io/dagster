---
title: Jira webhook alerts
description: Create bug tickets using the Jira Cloud REST API.
sidebar_position: 0
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

Automatically create tickets using the Jira Cloud REST API.

## Step 1: Set up authentication credentials

Create an Atlassian API Token in your [Atlassian profile](https://id.atlassian.com/manage-profile/security/api-tokens).

Atlassian requires Basic Auth encoded in Base64 (`email:token`).

**Mac/Linux Command**:

```bash
echo -n 'your_email@domain.com:your_api_token' | base64
```

Save the resulting Base64 string as an Environment Variable in Dagster+ (e.g. `ATLASSIAN_CREDENTIALS`).

## Step 2: Configure your alert notification

**Webhook Header**: In the Webhook configuration, set the following header:

- **Key**: `Authorization`
- **Value**: `Basic {{env.ATLASSIAN_CREDENTIALS}}`

**Webhook URL**: Use `https://<your-domain>.atlassian.net/rest/api/3/issue` as the URL for your alert webhook.

**Webhook Body**: Build the issue body using [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/):

```json
{
  "fields": {
    "project": {"key": "ENG"},
    "issuetype": {"name": "Bug"},
    "priority": {"name": "High"},
    "summary": "Dagster Alert: {{alert_summary}}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "Details:\n",
              "marks": [{"type": "strong"}]
            },
            {
              "type": "text",
              "text": "{{alert_content}}",
              "marks": [{"type": "code"}]
            }
          ]
        },
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "text": "View in Dagster",
              "marks": [{"type": "link", "attrs": {"href": "{{deployment_url}}"}}]
            }
          ]
        }
      ]
    }
  }
}
```

## Official References

- [Jira REST API v2 (Legacy)](https://developer.atlassian.com/cloud/jira/platform/rest/v2/intro/): Reference for simple text payloads.
- [Jira REST API v3 (Latest)](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/): Reference for ADF payloads.
- [ADF Playground](https://developer.atlassian.com/cloud/jira/platform/apis/document/playground/): Tool to design and validate rich text JSON payloads.
