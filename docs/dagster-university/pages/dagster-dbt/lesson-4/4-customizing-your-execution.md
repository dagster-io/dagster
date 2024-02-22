---
title: 'Lesson 4: Customizing your execution'
module: 'dagster_dbt'
lesson: '4'
---

# Customizing your execution

When looking at the asset catalog's page for a dbt model, you might notice the dbt code embedded into the description. This is an easy way to get a high-level understanding of the query, but it doesn't show you what the SQL query that dbt is running will look like, with the jinja templating resolved. This is because the asset description is defined when the code location is *loaded* and not during *runtime* when the dbt model is compiled and ran. Let's make some changes so you can see what SQL dbt is executing at runtime, while also showing you some patterns on how to customize what happens in a `@dbt_assets` definition.

We'll refactor the body of the `@dbt_assets` definition to fetch dbt's `run_results.json` artifact from your completed run and print the compiled SQL code for each dbt model. This will give you a better understanding of what dbt is doing under the hood.

Make the following changes:

1. Right now, you're immediately yielding all the results of your `dbt.cli()` execution. This execution contains a lot of context and metadata that we want, but it's currently inaccessible because we're not storing it. Let's refactor the `@dbt_assets` definition to store the `dbt.cli()` invocation in a variable called `dbt_build_invocation`.
   ```python
    dbt_build_invocation = dbt.cli(["build"], context=context)
    ```
2. Next, we'll yield from the `dbt_build_invocation.stream()` to get the logs from the `dbt` command. This will ensure that we replicate the functionality that originally had by yielding all of the events from the `dbt` command.
   ```python
   dbt_build_invocation = dbt.cli(["build"], context=context)

   yield from dbt_build_invocation.stream()
   ```
3. Because we stored the execution of `dbt.cli()` in `dbt_build_invocation`, we can now access the rest of our dbt artifacts. We'll use `dbt_build_invocation.get_artifact("run_results.json")` to get the `run_results.json` artifact. This artifact contains information like how long the run took, the number of models that were compiled, and the compiled SQL code for each model.
   ```python
   dbt_build_invocation = dbt.cli(["build"], context=context)

   yield from dbt_build_invocation.stream()

   run_results_json = dbt_build_invocation.get_artifact("run_results.json")
   ```
4. Finally, we'll loop through the `run_results_json` and print the compiled SQL code for each model. We'll access Dagster's logger from the `context` argument and use it to print the compiled SQL code to the `DEBUG` log level.
   ```python
   dbt_build_invocation = dbt.cli(["build"], context=context)

   yield from dbt_build_invocation.stream()

   run_results_json = dbt_build_invocation.get_artifact("run_results.json")
   for result in run_results_json["results"]:
       context.log.debug(result["compiled_code"])
   ```

Once you've made these changes, restart your code location and run any of your dbt models. You should see the compiled SQL code for each model in the logs.

This is the tip of the iceberg of what you can do in a `@dbt_assets` definition. For example, you can report back the metadata of your dbt runs to other services that may be dbt-specific.