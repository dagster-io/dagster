---
title: "Lesson 7: Overview"
module: 'dbt_dagster'
lesson: '7'
---

# Overview

At this point, you have a fully integrated Dagster and dbt project! You’ve learned how to load dbt models as Dagster assets, create dependencies, add partitions, and execute and monitor the resulting pipeline in the Dagster UI.

In this lesson, we’ll deploy your Dagster and dbt project to have it running in both local and production environments. We’ll walk through some considerations involved in bundling your dbt project up with Dagster.

You’ll learn how to deploy your unified Dagster and dbt project to production, including pushing the project to GitHub and setting up CI/CD to factor in your dbt project. We’ll use Dagster+ because it’s a standardized and controlled experience that we can walk you through, but all of the general patterns can be applied to however you deploy Dagster.
