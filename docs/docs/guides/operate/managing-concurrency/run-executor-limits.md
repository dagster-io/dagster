---
title: Run executor limits
description: Configuring the run executor to limit concurrency.
sidebar_position: 300
---

While [concurrency pool limits](/guides/operate/managing-concurrency/concurrency-pools) allow you to [limit the number of ops executing across all runs](/guides/operate/managing-concurrency/concurrency-pools#limit-the-number-of-assets-or-ops-actively-executing-across-all-runs), to limit the number of ops or assets executing _within a single run_, you need to configure your [run executor](/guides/operate/run-executors). You can limit concurrency for ops and assets in runs by using `max_concurrent` in the run config, either in Python or using the Launchpad in the Dagster UI.

:::info

The default limit for op execution within a run depends on which [run executor](/guides/operate/run-executors) you are using. For example, the <PyObject section="execution" module="dagster" object="multiprocess_executor" /> by default limits the number of ops executing to the value of `multiprocessing.cpu_count()` in the launched run.

:::

## Limit concurrent execution for a specific job

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/limit_execution_job.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

## Limit concurrent execution for all runs in a code location

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/limit_execution_code_location.py"
  language="python"
  title="src/<project_name>/defs/executor.py"
/>

## Limit by tag within a single run

Tag-based concurrency limits ops with specific tags, allowing fine-grained control within a run. Multiple ops can run in parallel, but only N with a given tag. This is useful when different ops in the same run have different resource requirements.

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/managing_concurrency/tag_concurrency.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>
