---
title: "Build pipelines with Scala and Spark"
description: "Learn to integrate Dagster Pipes with Scala and Spark to orchestrate Spark and Scala jobs in a Dagster pipeline."
sidebar_position: 71
---

This tutorial is focused on using Dagster Pipes to launch & monitor Apache Spark jobs implemented in Scala. The [Spark integration page](/integrations/libraries/spark) provides more information on using Pipes with specific Spark providers, such as AWS EMR or Databricks.

Spark is often used with object stores such as Amazon S3. In our example, Dagster will use an S3
bucket to communicate with the Apache Spark (sending data to the Spark application, as well as reading logs and results 
from Spark)

## Prerequisites

- An [AWS S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.html) to be used for communication between Spark and Dagster (and the corresponding `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).
- We are going to use [Docker](https://docs.docker.com/get-started/get-docker/) to emulate a typical Spark setup locally.
  This includes Apache Spark, the Java SDK, as well as the required Dagster libraries to run a development orchestration server.

## Production considerations

For demonstration purposes, this tutorial makes a few simplifications that you should consider when deploying in production:

- We are going to be running Spark in local mode, sharing the same container with Dagster. In production, consider having two separate environments:

  - **In the Dagster environment**, you'll need to have the following Python packages:

    - `dagster`
    - `dagster-webserver` --- to run the Dagster UI
    - `dagster-aws` --- when using S3

    You will also need to make the orchestration code available to Dagster (typically via a [code location](/guides/deploy/code-locations/)).

  - **In the Spark environment**, you'll need a suitable Scala compiler (we are using [gradle](https://gradle.org/)) and typically also the Java AWS S3 SDK packages. For example:

    ```shell
    curl -fSL "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.5.1/hadoop-aws-3.5.1.jar" \
      -o /opt/bitnami/spark/jars/hadoop-aws-3.5.1.jar

    curl -fSL "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.780/aws-java-sdk-bundle-1.12.780.jar" \
      -o /opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.780.jar
    ```

    Make sure `hadoop-aws` JAR and AWS Java SDK versions are compatible with your Spark/Hadoop build.

- In our example, the Scala jar will be built by docker before Spark start running. In production,
  consider building and uploading the JAR to Spark via CI/CD.

## Project Outline

```
.
├── Dockerfile
├── docker-compose.yml
├── dagster_code.py
├── external_scala
│   ├── build.gradle
│   ├── gradle.properties
│   ├── settings.gradle
│   ├── gradlew
│   └── src/main/scala/org/examples
│       └── Example.scala
│   └── build/libs
│       └── external_scala-all.jar
```

- `dagster_code.py` will contain the Dagster orchestration code.
- `Example.scala` will contain the Spark code to calculate pi, as well as the code to send message to Dagster.
- `gradlew` is the gradle wrapper (a script that downloads gradle on demand - this is the recommended way to use gradle).
- `build.gradle` contains all the build instructions to build and package `Example.scala` into a suitable jar for submission to Spark.
- `build/libs/external_scala-all.jar` is the output of this build process (created automatically by `docker build`).
- `Dockerfile` and `docker-compose.yml` allow for running this example in a reproducible environment using `docker compose`.

## Step 1: Writing the Dagster orchestration code (dagster_code.py)

We will set up a few non-default Pipes components to streamline the otherwise challenging problem of orchestrating Spark jobs.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/scalaspark/dagster_code.py">

* Notice that we are using S3 to pass Pipes messages from the Spark job to Dagster - so we create `PipesS3MessageReader` and `PipesS3ContextInjector` objects. (Technically, it's not strictly required to use S3 for passing the Dagster context, but storing it there will decrease the CLI arguments size).

* Notice we are using CLI arguments to pass the bootstrap information from Dagster to the Spark job. We will fetch them from the `session.get_bootstrap_cli_arguments` method. We pass these arguments to `spark-submit`.

:::note

In other Pipes workflows, passing the bootstrap information from Dagster to the remote Pipes session is typically done via environment variables, but setting environment variables for Spark jobs can be complicated (the exact way of doing this depends on the Spark deployment) or not possible at all. CLI arguments are a convenient alternative.

:::

## Step 2: Use Pipes in the Spark job (Example.scala)

Our example Spark workload (based on the [official example](https://github.com/apache/spark/blob/master/examples/src/main/scala/org/apache/spark/examples/SparkPi.scala)) will use Spark to calculate pi, and report the result back to Dagster.

First, create a new file name `Example.scala` in the `src/main/scala/org/examples` directory, then add the following code to create a context that can be used to send messages to Dagster:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/scalaspark/Example.scala" />

* Note how `PipesCliArgsParamsLoader` is used to load the CLI arguments passed by Dagster. This information will be used to automatically configure `PipesS3MessageWriter` and `PipesS3ContextLoader`.

* We are using the [Java Pipes Framework](https://github.com/dagster-io/community-integrations/tree/main/libraries/pipes/implementations/java) in our code (since Scala is fully compatible with Java libraries).

* `distributedCalculatePi` is the method actually doing the calculation. It also demonstrates sending messages and reporting results back to Dagster (with the methods `context.getLogger().info`, `context.reportAssetMaterialization`, and `reportAssetCheck`).

## Step 3: Create a Gradle Build File

We will also need `external_scala/settings.gradle` and `external_scala/build.gradle` files:

```
/* settings.gradle */

plugins {
    id 'org.gradle.toolchains.foojay-resolver-convention' version '0.9.0'
}

rootProject.name = 'external_scala'

```

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/scalaspark/build.gradle" />

* We are using the `shadow` plugin to create the jar (since our dependencies must be bundled in the JAR).

* Note that the `scala-library` and `spark-sql` dependencies are marked `compileOnly` - since Spark deployments
  already contain these libraries, they must be excluded from the JAR package.


## Step 4: Running the pipeline with Docker

1. Place the PySpark code for `script.py` and the Dagster orchestration code for `dagster_code.py` in the same directory.

2. Create a `Dockerfile` - notice that `./gradlew build` will run as part of `docker build`:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/scalaspark/Dockerfile" />

3. Create a `docker-compose.yml` - don't forget to update the environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/scalaspark/docker-compose.yml" />

4. Start the Dagster dev instance inside Docker:

```shell
docker compose up --build
```

5. Navigate to [http://localhost:3000](http://localhost:3000) to open the Dagster UI and materialize the asset. Metadata and logs from Spark will be available in Dagster!

