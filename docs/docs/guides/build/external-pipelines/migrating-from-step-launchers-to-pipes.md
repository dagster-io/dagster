---
title: "Migrating from Spark Step Launchers to Dagster Pipes"
description: "Learn how to migrate from Spark step launchers to Dagster Pipes."
sidebar_position: 80
---

In this guide, we’ll show you how to migrate from using step launchers to using [Dagster Pipes](index.md) in Dagster.

While step launchers were intended to support various runtime environments, in practice, they have only been implemented for Spark. Therefore, we will focus on Spark-related examples.

## Considerations

When deciding to migrate from step launchers to Dagster Pipes, consider the following:

- **Step launchers** are superceded by Dagster Pipes. While they are still available (and there are no plans for their removal), they are no longer the recommended method for launching external code from Dagster ops and assets. They won't be receiving new features or be under active development.
- **Dagster Pipes** is a more lightweight and flexible framework, but it does come with a few drawbacks:
* Spark runtime and the code executed will no longer be managed by Dagster for you.
* Dagster Pipes are not compatible with Resources and IO Managers. If you are heavily relying on these features, you might want to keep using step launchers.

## Steps

To migrate from step launchers to Dagster Pipes, you will have to perform the following steps.

### **1. Implement new CI/CD pipelines to prepare your Spark runtime environment**

Alternatively, this can be done from Dagster jobs, but either way, you will need to manage the Spark runtime yourself.

When running PySpark jobs, the following changes to Python dependencies should be considered:

- drop `dagster`
- add `dagster-pipes`

You can learn more about packaging Python dependencies for PySpark in [PySpark documentation](https://spark.apache.org/docs/latest/api/python/user_guide/python_packaging.html#python-package-management) or in the [AWS EMR Pipes](/guides/build/external-pipelines/aws/aws-emr-pipeline) guide.

The process of packaging the Python dependencies and scripts should be automated with a CI/CD pipeline and run before deploying the Dagster code location.

It's also possible to run Java or Scala Spark jobs with Dagster Pipes, but currently there is no official Pipes implementation for these languages. Therefore, forwarding Dagster events from these jobs is not yet supported officially (although it can be done with some custom code).

### **2. Update your Dagster code**

The goal is to keep the same observability and orchestration features while moving compute to an external script. Suppose you have existing code using step launchers similar to this:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/old_code.py" />

The corresponding Pipes code will instead have two components: the Dagster asset definition, and the external PySpark job.

Let's start with the PySpark job. The upstream asset will invoke the following script:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/upstream_asset_script.py" />

Now, we have to run this script from Dagster. First, let's factor the boilerplate EMR config into a reusable function:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/utils.py" startAfter="start_emr_config_marker" endBefore="end_emr_config_marker" />

Now, the asset body will be as follows:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/new_code.py" endBefore="after_upstream_marker" />

Since the asset now returns the Parquet file path, it will be saved by the `IOManager`, and the downstream asset will be able to access it.

Let's continue to migrating the second `downstream` asset.

Since we can't use IO Managers in scripts launched by Pipes, we would have to either make a CLI argument parser or use the handy `extras` feature provided by Pipes in order to pass this `"path"` value to the job. We will demonstrate the latter approach. The `downstream` asset turns into:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/new_code.py" startAfter="after_upstream_marker" endBefore="after_downstream_marker" />

Now, let's access the `path` value in the PySpark job:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/downstream_asset_script.py" />

Finally, provide the required resources to `Definitions`:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/new_code.py" startAfter="after_downstream_marker" />

# Conclusion

In this guide, we have demonstrated how to migrate from using step launchers to using Dagster Pipes. We have shown how to launch PySpark jobs on AWS EMR using `PipesEMRClient` and how to pass small pieces of data between assets using Dagster's metadata and Pipes extras.

# Supplementary

- [Dagster Pipes](index.md)
- [GitHub discussion](https://github.com/dagster-io/dagster/discussions/25685) on the topic
- [Dagster + Spark](/integrations/libraries/spark) - an up to date list of Pipes Clients for various Spark providers can be found here
- [AWS EMR Pipes tutorial](/guides/build/external-pipelines/aws/aws-emr-pipeline)
- [PipesEMRClient API docs](/api/python-api/libraries/dagster-aws#dagster_aws.pipes.PipesEMRClient)

:::note

**Heads up!** As an alternative to storing paths with an `IOManager`, the following utility function can be used to retrieve logged metadata values from upstream assets:

<CodeExample path="docs_snippets/docs_snippets/guides/migrations/from_step_launchers_to_pipes/utils.py" startAfter="start_metadata_marker" endBefore="end_metadata_marker" />

:::

