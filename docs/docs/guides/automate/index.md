---
title: 'Automate'
description: Learn how to automate your Dagster data pipelines.
sidebar_class_name: hidden
---

Automation is key to building reliable, efficient data pipelines. Dagster offers several ways to automate pipeline execution to fit a variety of needs.

Consider these factors when selecting an automation method:

- **Pipeline structure**: Are you working primarily with [assets](/guides/build/assets/), [ops](/guides/build/ops/), or a mix?
- **Timing requirements**: Do you need regular updates or event-driven processing?
- **Data characteristics**: Is your data partitioned? Do you need to update historical data?
- **System integration**: Do you need to react to external events or systems?

## Automation methods

<<<<<<< HEAD
| Method                                            | Description                                                                                                                  | Best for                                                     | Works with          |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------- |
| [Schedules](/guides/automate/schedules/)          | Run a [selection of assets](/guides/build/assets/asset-selection-syntax) at specified times with a cron expression           | Regular, time-based job runs and basic time-based automation | Assets, Ops, Graphs |
| [Declarative automation](declarative-automation/) | A framework that allows you to set automation conditions on assets and asset checks                                          | Asset-centric, condition-based updates                       | Assets only         |
| [Sensors](/guides/automate/sensors/)              | Trigger runs based on events or conditions that you define, like the arrival of a new file or a change to an external system | Event-driven automation                                      | Assets, Ops, Graphs |
| [Asset sensors](/guides/automate/asset-sensors)   | Trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.     | Cross-job/location asset dependencies                        | Assets only         |
| [GraphQL triggers](/guides/operate/graphql/)      | Trigger materializations and jobs from the GraphQL endpoint                                                                  | Event triggers from external systems                         | Assets, Ops, Jobs   |
=======
| Method | Description |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Schedules](schedules/) | Trigger jobs or a [selection of assets](/guides/build/assets/asset-selection-syntax) at specified times with a cron expression |
| [Declarative automation](declarative-automation/) | Trigger runs of assets or asset checks based on their status and dependencies |
| [Sensors](sensors/) | Trigger jobs or a selection of assets based on events or conditions that you define, like the arrival of a new file or a change to an external system |
| [Asset sensors](/guides/automate/asset-sensors) | Trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations. |
| [GraphQL triggers](/guides/operate/graphql/) | Trigger materializations and jobs from the GraphQL endpoint |

## Choosing an automation method

First, you should decide the _granularity_ of the automation method you want to use.

<Tabs>
  <TabItem value="Job-based Automation" label="job" default>
    With job-based automation, you first define [job](TODO) that contains the assets or ops that you want to execute. You can then configure your automation method to execute that job as a whole.

    This method is recommended when you have well-defined sections of your asset graph that execute on regular cadences. It provides a clear, predictable execution pattern where you can easily track the status of all related assets through a single job run. This makes it ideal for use cases where you want to maintain a straightforward, scheduled workflow with clear boundaries between different parts of your data pipeline.

  </TabItem>

  <TabItem value="Asset-based Automation" label="asset">
    With asset-based automation, each asset can be materialized independently of others. While the system will generally attempt to group multiple assets into the same run where possible, there are no guarantees on when individual assets will be materialized.

    This method is more flexible than job-based automation, and excels at handling complex dependency patterns between assets. It's particularly powerful when your assets have intricate interdependencies that don't fit neatly into predefined job boundaries. The system intelligently manages these relationships, ensuring that assets are materialized in the correct order while optimizing for efficiency. This approach gives you the freedom to let your asset graph's natural structure guide the execution flow, rather than forcing it into predetermined job boundaries.

  </TabItem>
</Tabs>
>>>>>>> ed70dcac3b ([docs][da] Update automate page)
