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

| Method                                            | Description                                                                                                                  
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- 
| [Schedules](schedules/)                           | Trigger jobs or a [selection of assets](/guides/build/assets/asset-selection-syntax) at specified times with a cron expression           
| [Declarative automation](declarative-automation/) | Trigger runs of assets or asset checks based on their status and dependencies 
| [Sensors](sensors/)                               | Trigger jobs or a selection of assets based on events or conditions that you define, like the arrival of a new file or a change to an external system 
| [Asset sensors](/guides/automate/asset-sensors)   | Trigger jobs when specified assets are materialized, allowing you to create dependencies between jobs or code locations.     
| [GraphQL triggers](/guides/operate/graphql/)      | Trigger materializations and jobs from the GraphQL endpoint                                                                  


## Choosing an automation method

First, you should decide the *granularity* of the automation method you want to use.  

<Tabs>
  <TabItem value="Job-based Automation" label="job" default>

    With job-based automation, you first define 

  </TabItem>

  <TabItem value="Asset-based Automation" label="asset">

  With asset based automation, each asset 

  This method is more flexible than job-based automation, but results in more independent runs being kicked off, as each asset can be materialized independently of others.

  </TabItem>
</Tabs>