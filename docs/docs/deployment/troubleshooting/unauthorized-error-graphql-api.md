---
title: UnauthorizedError in Dagster+ GraphQL API calls
sidebar_position: 170
description: Resolve UnauthorizedError when calling the Dagster+ GraphQL API by verifying endpoint URL, repository selector, and token configuration.
---

## Problem description

You receive an `UnauthorizedError` with Dagster+ GraphQL API calls even though you are using correct credentials.

## Root cause

Common causes of `UnauthorizedError` include:

- Incorrect endpoint URL
- Mismatched repository selector parameters
- Invalid or expired user token
- Insufficient token permissions

## Solution

When making GraphQL API calls to Dagster+, ensure your endpoint includes the deployment name (e.g., `/prod`) in the URL:

```text
https://[organization].dagster.cloud/prod/graphql
```

Verify your repository selector parameters match exactly with your Dagster+ deployment settings:

```graphql
repositorySelector: {
  repositoryName: "your_repository_name",
  repositoryLocationName: "your_location_name"
}
```

Finally, ensure you are using a correctly formatted API call by leveraging the Python GQL client:

```python
import gql
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(
    url="https://your-org.dagster.cloud/prod/graphql",
    headers={"Dagster-Cloud-Api-Token": YOUR_USER_TOKEN},
)

gql_client = gql.Client(transport=transport)
```

## Related documentation

- [Dagster GraphQL API documentation](/api/graphql)
- [Using the GraphQL client](/api/graphql/graphql-client#using-the-graphql-client)
