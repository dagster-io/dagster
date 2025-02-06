---
title: "Build pipelines in JavaScript"
sidebar_position: 20
---

This guide covers how to run JavaScript with Dagster using Pipes, however, the same principle will apply to other languages.

<details>
<summary>Prerequisites</summary>

To follow this guide, you'll need:

- Familiarity with [Assets](/guides/build/assets/)
- A basic understanding of JavaScript and Node.js

To run the examples, you'll need to install:

- [Node.js](https://nodejs.org/en/download/package-manager/)
- The following Python packages:

   ```bash
   pip install dagster dagster-webserver
   ```
- The following Node packages:
   ```bash
   npm install @tensorflow/tfjs
   ```
</details>

## Step 1: Create a script using Tensorflow in JavaScript

First, you'll create a JavaScript script that reads a CSV file and uses Tensorflow to train a sequential model.

Create a file named `tensorflow/main.js` with the following contents:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/non-python/pipes-contrived-javascript.js" language="javascript" title="tensorflow/main.js" />

## Step 2: Create a Dagster asset that runs the script

In Dagster, create an asset that:

- Uses the `PipesSubprocessClient` resource to run the script with `node`
- Sets the `compute_kind` to `javascript`. This makes it easy to identify that an alternate compute will be used for materialization.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/non-python/pipes-asset.py" language="python" />

When the asset is materialized, the stdout and stderr will be captured automatically and shown in the asset logs. If the command passed to Pipes returns a successful exit code, Dagster will produce an asset materialization result.

## Step 3: Send and receive data from the script

To send context to your script or emit events back to Dagster, you can use environment variables provided by the `PipesSubprocessClient`.


- `DAGSTER_PIPES_CONTEXT` - Input context
- `DAGSTER_PIPES_MESSAGES` - Output context

Create a new file with the following helper functions that read the environment variables, decode the data, and write messages back to Dagster:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/non-python/pipes-javascript-utility.js" language="javascript" />

Both environment variables are base64 encoded, zip compressed JSON objects. Each JSON object contains a path that indicates where to read or write data.

## Step 4: Emit events and report materializations from your external process

Using the utility functions to decode the Dagster Pipes environment variables, you can send additional parameters into the JavaScript process. You can also output more information into the asset materializations.

Update the `tensorflow/main.js` script to:

- Retrieve the model configuration from the Dagster context, and
- Report an asset materialization back to Dagster with model metadata

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/non-python/pipes-full-featured-javascript.js" language="javascript" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 5: Update the asset to provide extra parameters

Finally, update your Dagster asset to pass in the model information that's used by the script:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/non-python/pipes-asset-with-context.py" language="python" />

## What's next?

- Schedule your pipeline to run periodically with [Automating Pipelines](/guides/automate/index.md)
- Explore adding asset checks to validate your script with [Understanding Asset Checks](/guides/test/asset-checks)
