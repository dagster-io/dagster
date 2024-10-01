---
title: "Lesson 1: Why use dbt and Dagster together?"
module: 'dbt_dagster'
lesson: '1'
---

# Why use dbt and Dagster together?

At a glance, it might seem like Dagster and dbt do the same thing. Both technologies, after all, work with data assets and are instrumental in modern data platforms.

However, dbt Core can only transform data that is already in a data warehouse - it can’t extract from a source, load it into its final destination, or automate either of these operations. And while you could use dbt Cloud’s native features to schedule running your models, other portions of your data pipelines - such as Fivetran-ingested tables or data from Amazon S3 - won’t be included.

To have everything running together, you need an orchestrator. This is where Dagster comes in:

> Dagster’s core design principles go really well together with dbt. The similarities between the way that Dagster thinks about data pipelines and the way that dbt thinks about data pipelines means that Dagster can orchestrate dbt much more faithfully than other general-purpose orchestrators like Airflow.
>
> At the same time, Dagster is able to compensate for dbt’s biggest limitations. dbt is rarely used in a vacuum: the data transformed using dbt needs to come from somewhere and go somewhere. When a data platform needs more than just dbt, Dagster is a better fit than dbt-specific orchestrators, like the job scheduling system inside dbt Cloud. ([source](https://dagster.io/blog/orchestrating-dbt-with-dagster))

At a glance, using dbt alongside Dagster gives analytics and data engineers the best of both their worlds:

- **Analytics engineers** can author analytics code in a familiar language while adhering to software engineering best practices
- **Data engineers** can easily incorporate dbt into their organization’s wider data platform, ensuring observability and reliability

There’s more, however. Other orchestrators will provide you with one of two less-than-appealing options: running dbt as a single task that lacks visibility, or running each dbt model as an individual task and pushing the execution into the orchestrator, which goes against how dbt is intended to be run.

Using dbt with Dagster is unique, as Dagster separates data assets from the execution that produces them and gives you the ability to monitor and debug each dbt model individually.
