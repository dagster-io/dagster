---
title: 'Lesson 5: Overview'
module: 'dagster_dbt'
lesson: '5'
---

# Overview

In Lesson 3, you loaded your dbt project's models as assets into Dagster. You also materialized some of those models.

In this lesson, we’ll integrate more dbt models with the rest of your Dagster project. You’ll use the existing Dagster assets as sources in your dbt project and learn how to further customize how Dagster maps your dbt project with the `DagsterDbtTranslator` class. To wrap things up, we’ll show you how to automate the running of the dbt models in Dagster.