---
title: "Dagster GraphQL API"
description: Dagster exposes a GraphQL API that allows clients to interact with Dagster programmatically
sidebar_position: 60
---

:::note

The GraphQL API is still evolving and is subject to breaking changes. A large portion of the API is primarily for internal use by the [Dagster webserver](/guides/operate/webserver).
For any of the queries below, we will be clear about breaking changes in release notes.

:::


Dagster exposes a GraphQL API that allows clients to interact with Dagster programmatically. The API allows users to:

- Query information about Dagster runs, both historical and currently executing
- Retrieve metadata about repositories, jobs, and ops, such as dependency structure and config schemas
- Launch job executions and re-executions, allowing users to trigger executions on custom events

## Using the GraphQL API

The GraphQL API is served from the[webserver](/guides/operate/webserver). To start the server, run the following:

```shell
dagster dev
```

The webserver serves the GraphQL endpoint at the `/graphql` endpoint. If you are running the webserver locally on port 3000, you can access the API at [http://localhost:3000/graphql](http://localhost:3000/graphql).

### Using the GraphQL playground

You can access the GraphQL Playground by navigating to the `/graphql` route in your browser. The GraphQL playground contains the full GraphQL schema and an interactive playground to write and test queries and mutations:

![GraphQL playground](/images/guides/operate/graphql/playground.png)

### Exploring the GraphQL schema and documentation

Clicking on the **Docs** tab on the right edge of the playground opens up interactive documentation for the GraphQL API. The interactive documentation is the best way to explore the API and get information about which fields are available on the queries and mutations:

![GraphQL docs](/images/guides/operate/graphql/docs.png)

## Python client

Dagster also provides a Python client to interface with Dagster's GraphQL API from Python. For more information, see "[Dagster Python GraphQL client](graphql-client)".

## Example queries

- [Get a list of Dagster runs](#get-a-list-of-dagster-runs)
- [Get a list of repositories](#get-a-list-of-repositories)
- [Get a list of jobs within a repository](#get-a-list-of-jobs-within-a-repository)
- [Launch a run](#launch-a-run)
- [Terminate an in-progress run](#terminate-an-in-progress-run)

### Get a list of Dagster runs

<Tabs>
<TabItem value="Paginate through runs">

You may eventually accumulate too many runs to return in one query. The `runsOrError` query takes in optional `cursor` and `limit` arguments for pagination:

```shell
query PaginatedRunsQuery($cursor: String) {
  runsOrError(
    cursor: $cursor
    limit: 10
  ) {
    __typename
    ... on Runs {
      results {
        runId
        jobName
        status
        runConfigYaml
        startTime
        endTime
      }
    }
  }
}
```

</TabItem>
<TabItem value="Filtering runs">

The `runsOrError` query also takes in an optional filter argument, of type `RunsFilter`. This query allows you to filter runs by:

- run ID
- job name
- tags
- statuses

For example, the following query will return all failed runs:

```shell
query FilteredRunsQuery($cursor: String) {
  runsOrError(
    filter: { statuses: [FAILURE] }
    cursor: $cursor
    limit: 10
  ) {
    __typename
    ... on Runs {
      results {
        runId
        jobName
        status
        runConfigYaml
        startTime
        endTime
      }
    }
  }
}
```

</TabItem>
</Tabs>

### Get a list of repositories

This query returns the names and location names of all the repositories currently loaded:

```shell
query RepositoriesQuery {
  repositoriesOrError {
    ... on RepositoryConnection {
      nodes {
        name
        location {
          name
        }
      }
    }
  }
}
```

### Get a list of jobs within a repository

Given a repository, this query returns the names of all the jobs in the repository.

This query takes a `selector`, which is of type `RepositorySelector`. A repository selector consists of both the repository location name and repository name.

```shell
query JobsQuery(
  $repositoryLocationName: String!
  $repositoryName: String!
) {
  repositoryOrError(
    repositorySelector: {
      repositoryLocationName: $repositoryLocationName
      repositoryName: $repositoryName
    }
  ) {
    ... on Repository {
      jobs {
        name
      }
    }
  }
}
```

### Launch a run

To launch a run, use the `launchRun` mutation. Here, we define `LaunchRunMutation` to wrap our mutation and pass in the required arguments as query variables. For this query, the required arguments are:

- `selector` - A dictionary that contains the repository location name, repository name, and job name.
- `runConfigData` - The run config for the job execution. **Note**: Note that `runConfigData` is of type `RunConfigData`. This type is used when passing in an arbitrary object for run config. This is any-typed in the GraphQL type system, but must conform to the constraints of the config schema for this job. If it doesn't, the mutation returns a `RunConfigValidationInvalid` response.

```shell
mutation LaunchRunMutation(
  $repositoryLocationName: String!
  $repositoryName: String!
  $jobName: String!
  $runConfigData: RunConfigData!
) {
  launchRun(
    executionParams: {
      selector: {
        repositoryLocationName: $repositoryLocationName
        repositoryName: $repositoryName
        jobName: $jobName
      }
      runConfigData: $runConfigData
    }
  ) {
    __typename
    ... on LaunchRunSuccess {
      run {
        runId
      }
    }
    ... on RunConfigValidationInvalid {
      errors {
        message
        reason
      }
    }
    ... on PythonError {
      message
    }
  }
}
```

### Terminate an in-progress run

If you want to stop execution of an in-progress run, use the `terminateRun` mutation. The only required argument for this mutation is the ID of the run.

```shell
mutation TerminateRun($runId: String!) {
  terminateRun(runId: $runId){
    __typename
    ... on TerminateRunSuccess{
      run {
        runId
      }
    }
    ... on TerminateRunFailure {
      message
    }
    ... on RunNotFoundError {
      runId
    }
    ... on PythonError {
      message
      stack
    }
  }
}
```
