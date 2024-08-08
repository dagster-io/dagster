---
title: 'Lesson 4: Speeding up the development cycle'
module: 'dagster_dbt'
lesson: '4'
---

# Speeding up the development cycle

By now, you’ve had to run `dbt parse` to create the manifest file and reload your code location quite frequently, which doesn’t feel like the cleanest developer experience.

Before we move on, we’ll reduce the number of steps in the feedback loop. We'll automate the creation of the manifest file by taking advantage of the `dbt_project` representation that we wrote earlier.

---

## Automating creating the manifest file in development

The first detail is that the `dbt_project` doesn’t need to be part of an asset to be executed. This means that once a `dbt_project` is defined, you can use it to execute commands when your code location is being built. Rather than manually running `dbt parse`, let’s use the `dbt_project` to prepare the manifest file for us.

In `project.py`, after the code initializing `dbt_project`, add the following code:

```python
dbt_project.prepare_if_dev()
```

If you look at the dbt project’s `/target` directory, you’ll see it stores the artifacts. When you use `dagster dev` in local development and you reload your code, you'll see that a new manifest file is generated.

The `prepare_if_dev()` method automatically prepares your dbt project at run time during development, meaning you no longer have to run `dbt parse`! The preparation process works by pulling the dbt project's dependencies and reloading the manifest file to detect any changes.

Reload your code location in the Dagster UI, and you’ll see that everything should still work: the dbt models are still shown as assets and you can manually materialize any of the models. 

---

## Creating the manifest for production

This is great, however, it only handles the preparation of a new manifest file in local development. In production, where a dbt project is stable, we may want to prepare a new manifest file only at build time, during the deployment process. This can be done using the command line interface (CLI) available in the `dagster_dbt` package.

Don't worry about the details for now! In Lesson 7, we’ll discuss the details on how to create a manifest file programmatically during deployment using the `dagster_dbt` CLI.
