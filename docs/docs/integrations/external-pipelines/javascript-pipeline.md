---
description: Learn to run JavaScript with Dagster using Dagster Pipes.
sidebar_position: 20
title: JavaScript pipelines
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

:::info

For production pipelines, we recommend using the [`@dagster-io/dagster-pipes` npm package](https://www.npmjs.com/package/@dagster-io/dagster-pipes), which enables integration between any TypeScript process and Dagster.

:::

This guide covers how to run JavaScript with Dagster using Pipes, however, the same principle will apply to other languages.

## Prerequisites

To run the examples, you'll need to:

- Create a new Dagster project:
  <ScaffoldProject />
- Install [Node.js](https://nodejs.org/en/download/package-manager)
- Add the following Node packages:
  ```bash
  npm install @tensorflow/tfjs
  ```

## Step 1: Create a script using Tensorflow in JavaScript

First, you'll create a JavaScript script that reads a CSV file and uses Tensorflow to train a sequential model.

Create a file named `tensorflow/main.js` with the following contents:

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/pipes-contrived-javascript.js"
  language="javascript"
  title="src/<project_name>/defs/tensorflow/main.js"
/>

## Step 2: Create a Dagster asset that runs the script

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In Dagster, create an asset that:

- Uses the `PipesSubprocessClient` resource to run the script with `node`
- Sets the `compute_kind` to `javascript`. This makes it easy to identify that an alternate compute will be used for materialization.

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/pipes-asset.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

When the asset is materialized, the stdout and stderr will be captured automatically and shown in the asset logs. If the command passed to Pipes returns a successful exit code, Dagster will produce an asset materialization result.

## Step 3: Define a Definitions object

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

To make the resource loadable and accessible, such as the CLI, UI, and Dagster+, you’ll create a function with the <PyObject section="definitions" module="dagster" object="Definitions" decorator />.

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/resources.py"
  language="python"
  title="src/<project_name>/defs/resources.py"
/>

## Step 4: Send and receive data from the script

To send context to your script or emit events back to Dagster, you can use environment variables provided by the `PipesSubprocessClient`.

- `DAGSTER_PIPES_CONTEXT` - Input context
- `DAGSTER_PIPES_MESSAGES` - Output context

Create a new file with the following helper functions that read the environment variables, decode the data, and write messages back to Dagster:

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/pipes-javascript-utility.js"
  language="javascript"
  title="src/<project_name>/defs/tensorflow/main.js"
/>

Both environment variables are base64 encoded, zip compressed JSON objects. Each JSON object contains a path that indicates where to read or write data.

## Step 5: Emit events and report materializations from your external process

Using the utility functions to decode the Dagster Pipes environment variables, you can send additional parameters into the JavaScript process. You can also output more information into the asset materializations.

Update the `tensorflow/main.js` script to:

- Retrieve the model configuration from the Dagster context, and
- Report an asset materialization back to Dagster with model metadata

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/pipes-full-featured-javascript.js"
  language="javascript"
  title="src/<project_name>/defs/tensorflow/main.js"
/>

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

## Step 6: Update the asset to provide extra parameters

Finally, update your Dagster asset to pass in the model information that's used by the script:

<CodeExample
  path="docs_snippets/docs_snippets/guides/non-python/pipes-asset-with-context.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>

## What's next?

- Schedule your pipeline to run periodically with [Automating Pipelines](/guides/automate)
- Explore adding asset checks to validate your script with [Understanding Asset Checks](/guides/test/asset-checks)
