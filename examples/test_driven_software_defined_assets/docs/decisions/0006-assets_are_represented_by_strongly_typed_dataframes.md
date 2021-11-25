# 5. Assets are represented by strongly typed dataframes

* **Status**: Proposed <br/>
* **Date**: 2021-11-25 <br/>
* **Deciders**: David Laing <br/>

## Context

Usability of Data Assets increases when they are well documented and don't contain any unexpected data.

Having inconsistent / out of date documentation is often worse than having no documentation.

## Decision

Each Asset will be represented by a strongly typed dataframe based on [`dagster_pandas`](https://docs.dagster.io/integrations/pandas).  

The strongly typed dataframe class for each Asset is:

* the source of truth for the asset's schema (including field types, allowed values and documentation)
* used to validate the asset's data on every job run 
* used to generate documentation for the Asset

## Consequences

