# 2. Software Defined Assets and Dagster

* **Status**: Decided <br/>
* **Date**: 2021-11-19 <br/>
* **Deciders**: David Laing <br/>

## Context

The `consumption_datamart` is a long-lived data asset that will be used by multiple internal teams as the source of truth for consumption reporting
on ACME's product subscriptions.  Since key business decisions will be made & measured based on its data it needs to be trusted, well documented and
maintained over time.

## Decision

We treat the `consumption_datamart` like a software product; using common software engineering techniques to build automation that keeping the
data quality high over time while reducing the ongoing maintenance costs.

Specifically we will:

* Capture and validate requirements using an automated test suite
* Build on top of the Open Source [Dagster framework](https://github.com/dagster-io/dagster)
* Automate the ongoing maintenance of the data assets
* Document & share the data assets via Dagit

## Consequences

Initial development time / costs of the Data Mart will be slower / higher that manually curating a point in time dataset.

However, ongoing maintenance & upkeep of the dataset will be significantly lower & faster due to it being automated.
