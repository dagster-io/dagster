---
title: 'Automating pipelines'
description: Learn how to automate your data pipelines.
sidebar_position: 40
sidebar_class_name: hidden
---

Automation is key to building reliable, efficient data pipelines. This guide provides a simplified overview of the main ways to automate processes in Dagster, helping you choose the right method for your needs. You will find links to more detailed guides for each method below.

<details>
  <summary>Prerequisites</summary>

Before continuing, you should be familiar with:

- [Asset definitions](/guides/build/assets-concepts/index.mdx
- [Jobs](/guides/build/ops-jobs)

</details>

## Automation methods overview

Dagster offers several ways to automate pipeline execution:

1. [Schedules](#schedules) - Run jobs at specified times
2. [Sensors](#sensors) - Trigger runs based on events
3. [Asset Sensors](#asset-sensors) - Trigger jobs when specific assets materialize
4. [GraphQL Endpoint](#graphql-endpoint) - Trigger materializations and jobs from the GraphQL endpoint

## How to choose the right automation method

Consider these factors when selecting an automation method:

1. **Pipeline Structure**: Are you working primarily with assets, ops, or a mix?
2. **Timing Requirements**: Do you need regular updates or event-driven processing?
3. **Data Characteristics**: Is your data partitioned? Do you need to update historical data?
4. **System Integration**: Do you need to react to external events or systems?

Use this table to help guide your decision:

| Method                 | Best For                               | Works With          |
| ---------------------- | -------------------------------------- | ------------------- |
| Schedules              | Regular, time-based job runs           | Assets, Ops, Graphs |
| Sensors                | Event-driven automation                | Assets, Ops, Graphs |
| Declarative Automation | Asset-centric, condition-based updates | Assets only         |
| Asset Sensors          | Cross-job/location asset dependencies  | Assets only         |
| GraphQL Triggers       | Event triggers from external systems   | Assets, Ops, Jobs   |

## Schedules

Schedules allow you to run jobs at specified times, like "every Monday at 9 AM" or "daily at midnight."
A schedule combines a selection of assets, known as a [Job](/guides/build/ops-jobs), and a [cron expression](https://en.wikipedia.org/wiki/Cron)
to define when the job should be run.

To make creating cron expressions easier, you can use an online tool like [Crontab Guru](https://crontab.guru/).

### When to use schedules

- You need to run jobs at regular intervals
- You want basic time-based automation

For examples of how to create schedules, see [How-To Use Schedules](/guides/automate/schedules).

For more information about how Schedules work, see [About Schedules](/guides/automate/schedules).

## Sensors

Sensors allow you to trigger runs based on events or conditions that you define, like a new file arriving or an external system status change.

You must provide a function that the sensor will use to determine if it should trigger a run.

Like schedules, sensors operate on a selection of assets, known as [Jobs](/guides/build/ops-jobs) and can either start a pipeline through a Run or log a reason for not starting a pipeline using a SkipReason.

### When to use sensors

- You need event-driven automation
- You want to react to changes in external systems

For more examples of how to create sensors, see the [How-To Use Sensors](/guides/automate/sensors) guide.

For more information about how sensors work, see the [About Sensors](/guides/automate/sensors) concept page.

## Asset sensors

Asset Sensors trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.

### When to use Asset sensors

- You need to trigger jobs based on asset materializations
- You want to create dependencies between different jobs or code locations

For more examples of how to create asset sensors, see the [How-To Use Asset Sensors](/guides/automate/asset-sensors) guide.

## Declarative Automation

{/** TODO: add content **/}

## GraphQL Endpoint

It is possible to trigger asset materializations in a job from external services using the GraphQL endpoint.

### When to use the GraphQL endpoint

- You want to integrate Dagster with an external system or tool
- You need to trigger a materialization or job over an HTTP endpoint
- You are creating a custom script for batching operations

### Triggering a job

To trigger a job to run using the GraphQL endpoint in Dagster, you can use the `launchRun` mutation. Here's an example using the `requests` library:

```python
import requests


graphql_endpoint = "http://localhost:3000/graphql"

query = """
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
"""

response = requests.post(
    graphql_endpoint,
    json={
        "query": query,
        "variables": {
            "repositoryLocationName": "<replace-with-code-location-name>",
            "repositoryName": "__repository__",  # default if using `Definitions`
            "jobName": "<replace-with-job-name>",
            "runConfigData": {},
        },
    },
)
```

### Triggering an asset materialization

To trigger an asset materialization using the GraphQL endpoint in Dagster, you can use the `LaunchPipelineExecution` mutation. Here's an example using the `requests` library:

```python
import requests


graphql_endpoint = "http://localhost:3000/graphql"

query = """
mutation LaunchPipelineExecution(
    $executionParams: ExecutionParams!
) {
  launchPipelineExecution(executionParams: $executionParams) {
    ... on LaunchRunSuccess {
      run {
        id
        pipelineName
        __typename
      }
      __typename
    }
    ... on PipelineNotFoundError {
      message
      __typename
    }
    ... on InvalidSubsetError {
      message
      __typename
    }
    ... on RunConfigValidationInvalid {
      errors {
        message
        __typename
      }
      __typename
    }
  }
}
"""

response = requests.post(
    graphql_endpoint,
    json={
        "query": query,
        "variables": {
            "executionParams": {
                "mode": "default",
                "runConfigData": "{}",
                "selector": {
                    "assetCheckSelection": [],
                    "assetSelection": [{"path": ["<replace-with-asset-key>"]}],
                    "pipelineName": "__ASSET_JOB",
                    "repositoryLocationName": "<replace-with-code-location-name>",
                    "repositoryName": "__repository__",
                },
            }
        },
    },
)
```

## Next steps

- Learn more about [advanced scheduling patterns] - {/** TODO ADD LINK **/}
- Explore [complex sensor examples] - {/** TODO ADD LINK **/}
- Dive into [Declarative Automation best practices] - {/** TODO ADD LINK **/}

By understanding and effectively using these automation methods, you can build more efficient data pipelines that respond to your specific needs and constraints.
