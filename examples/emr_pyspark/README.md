---
title: emr_pyspark
description: Example of running a PySpark solid in EMR
---

# Submitting PySpark solids on EMR

This example demonstrates how to have a solid run as a Spark step on an EMR cluster.  In it, each
of the three solids will be executed as a separate EMR step on the same EMR cluster.

It accomplishes this by using the `emr_pyspark_step_launcher`, which knows how to launch an EMR step
that runs the contents of a solid.  The example defines a mode that links the resource key
"pyspark_step_launcher" to the `emr_pyspark_step_launcher` resource definition, and then requires
that "pyspark_step_launcher" resource key for the solid which it wants to launch remotely.

`prod_resources.yaml` demonstrates how to configure an emr_pyspark_step_launcher.

The EMR PySpark step launcher relies on the presence of an s3_resource and s3 intermediate store to
shuttle config and events to and from EMR.

More generally, a step launcher is any resource that extends the StepLauncher abstract class,
whose methods can be invoked where a solid would otherwise be executed in-process to instead launch
a remote process with the solid running inside it.  To use a step launcher for a particular solid,
set a required resource key for the solid that points to that resource.


# Open in Playground

Open up this example in a playground using [Gitpod](https://gitpod.io)

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#EXAMPLE=emr_pyspark/https://github.com/dagster-io/dagster)

# Download Manually

Download the example:

```
curl https://codeload.github.com/dagster-io/dagster/tar.gz/master | tar -xz --strip=2 dagster-master/examples/emr_pyspark
cd dep_dsl
```
