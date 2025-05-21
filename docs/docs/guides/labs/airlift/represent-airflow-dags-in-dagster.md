---
title: Represent Airflow DAGs in Dagster
description: Represent Airflow DAGs in Dagster.
sidebar_position: 200
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';
import AirliftPrereqs from '@site/docs/partials/\_AirliftPrereqs.md';

<AirliftPreview />

TK - conceptual info here

once you have represented your airflow instance in dagster using the airflow instance component, you may want to represent the graph of asset dependencies produced by that dag as well. this is easy to do in your component configuration.

## Manually mapping assets to Airflow tasks

You can manually define which assets are produced by a given airflow dag by editing your component's yaml configuration:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift_v2/represent_airflow_dags_in_dagster/component_dag_mappings.yaml" />

If you have a more specific mapping from a task within the dag to a set of assets, you can also set these mappings at the task level:

<CodeExample path="docs_snippets/docs_snippets/integrations/airlift_v2/represent_airflow_dags_in_dagster/component_task_mappings.yaml" />

## Prerequisites

<AirliftPrereqs />