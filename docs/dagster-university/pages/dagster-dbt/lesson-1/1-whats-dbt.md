---
title: "Lesson 1: What's dbt?"
module: 'dbt_dagster'
lesson: '1'
---

# What's dbt?

In the world of ETL/ELT, dbt - that’s right, all lowercase - is the ‘T’ in the process of Extracting, Loading, and **Transforming** data. Using familiar languages like SQL and Python, dbt is open-source software that allows users to write and run data transformations against the data loaded into their data warehouses.

Before we go any further, let’s take a look at how the folks at dbt describe their product:

> dbt is a transformation workflow that helps you get more work done while producing higher quality results. You can use dbt to modularize and centralize your analytics code, while also providing your data team with guardrails typically found in software engineering workflows. Collaborate on data models, version them, and test and document your queries before safely deploying them to production, with monitoring and visibility.
>
> dbt compiles and runs your analytics code against your data platform, enabling you and your team to collaborate on a single source of truth for metrics, insights, and business definitions. This single source of truth, combined with the ability to define tests for your data, reduces errors when logic changes, and alerts you when issues arise. ([source](https://docs.getdbt.com/docs/introduction))

---

## Why use dbt?

dbt isn’t popular only for its easy, straightforward adoption, but also because it embraces software engineering best practices. Data analysts can use skills they already have - like SQL expertise - and simultaneously take advantage of:

- **Keeping things DRY** (**Don’t Repeat Yourself).** dbt models, which are business definitions represented in SQL `SELECT` statements, can be referenced in other models. Focusing on modularity allows you to reduce bugs, standardize analytics logic, and get a running start on new analyses.
- **Automatically managing dependencies and generating documentation.** Dependencies between models are not only easy to declare, they’re automatically managed by dbt. Additionally, dbt also generates a DAG (directed acyclic graph), which shows how models in a dbt project relate to each other.
- **Preventing negative impact on end-users.** Support for multiple environments ensures that development can occur without impacting users in production.

Dagster’s approach to building data platforms maps directly to these same best practices, making dbt and Dagster a natural, powerful pairing. In the next section, we’ll dig into this a bit more.
