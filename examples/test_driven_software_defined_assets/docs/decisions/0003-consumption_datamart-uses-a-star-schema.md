# 3. consumption_datamart uses a star schema

* **Status**: Decided <br/>
* **Date**: 2021-11-19 <br/>
* **Deciders**: David Laing <br/>

## Context

The `consumption_datamart` needs a schema that facilitates curating & reporting on Entitlement and Usage facts with a daily grain.

## Decision

The `consumption_datamart`  follows the simplest of the DataWareHouse schema options - a [star schema](https://en.wikipedia.org/wiki/Star_schema) made up of:

* [Fact tables](https://en.wikipedia.org/wiki/Star_schema#Fact_tables) (with prefix `fact_`) that record measurements or metrics for a specific event
* [Dimensions tables](https://en.wikipedia.org/wiki/Star_schema#Dimension_tables) (with prefix `dim_`) that store common attributes related to facts
  and enable fact aggregation and joining to other datasets
* exposed with a [daily grain](https://www.kimballgroup.com/2003/03/declaring-the-grain/)

## Consequences

A star schema should be familiar to most data analysts; enabling simpler queries & reporting logic.

However, it isn't the most storage space efficient approach.

See https://en.wikipedia.org/wiki/Star_schema for further benefits, disadvantages and examples
