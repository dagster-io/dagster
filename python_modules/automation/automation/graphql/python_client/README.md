# Using `dagster-graphql-client` cli

The `dagster-graphql-client` cli is used for commands related to the Dagster GraphQL Python client.
It is currently used to make sure that the current iteration of the client's GraphQL queries are accounted for in
the Dagster GraphQL server's backwards compatability testing.

## Setup

```
    pip install \
    -e python_modules/dagster-graphql \
    -e python_modules/automation \
```

or `make dev_install` should do the trick! After that `dagster-graphql-client` should be accessible
for the command line.

## Usage

### `dagster-graphql-client query check`

Run `dagster-graphql-client query check` to check if the current GraphQL queries used by the
Dagster GraphQL client are accounted for in the query snapshot directory
(located at `dagster-graphql:dagster_graphql_tests.graphql.client_backcompat.query_snapshots`)
used by the GraphQL server's backwards compatability test suite for the Python Client.

If `dagster-graphql-client query check` runs into errors, fix them manually or run `dagster-graphql-client query snapshot`.

`dagster-graphql-client query check` is run as a Buildkite check to ensure that changes to the queries
used by the Dagster GraphQL client are always accounted for in future backcompatability testing.

### `dagster-graphql-client query snapshot`

Running `dagster-graphql-client query snapshot` takes a snapshot of the current version of queries
used by the Dagster GraphQL client and stores them in the query snapshot directory
(`dagster-graphql:dagster_graphql_tests.graphql.client_backcompat.query_snapshots`)
for use in backwards compatability testing in the future.