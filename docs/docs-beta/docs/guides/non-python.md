---
title: "External Compute"
sidebar_label: "Dagster Pipes"
sidebar_position: 60
---

Dagster is written in Python, but that doesn't mean it's that Python is the only language that can be used when materializing assets. With Pipes, you can run code in other languages and send information back forth with Dagster. This guide covers how to run JavaScript with Dagster using Pipes, however, the same principle will apply to other languages.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- A basic understanding of JavaScript and Node.js
</details>

## Create a script using Tensorflow in JavaScript

{/* TODO: consider changing guide to step-based-guide template */}

In this example, we will orchestrate a JavaScript script that reads in a CSV file, and uses the Tensorflow  to train a sequential model using Dagster Pipes.

Start by creating a file named `tensorflow/main.js` with the following contents:

<CodeExample filePath="guides/non-python/pipes-contrived-javascript.js" language="javascript" title="tensorflow/main.js" />

## Create a Dagster asset that runs your script

Create an asset that takes the `PipesSubprocessClient` resource, and set the `compute_kind` so that we know an alternate compute is being used for materialization. Then, use the resource to run your script using `node`.

:::note
You will need `node` in the environment you are running Dagster, along with Tensorflow installed.
:::

{/* TODO: consider adding instructions for installing dependencies */}

<CodeExample filePath="guides/non-python/pipes-asset.py" language="python" title="Asset using Dagster Pipes." />

The stdout and stderr will be captured automatically and shown in the asset logs. If the command passed to Dagster Pipes returns a successful exit code, then an asset materialization result will be produced.

![Image of captured stdout](/img/placeholder.svg)

## Send to, and receive data from, your script (Optional)

Optionally, you may want to send context to your script, or emit events back to Dagster. This can be done through environment variables that are provided by the `PipesSubprocessClient`.

The two environment variables specify a path to a file&mdash;one for input and one for output:

- `DAGSTER_PIPES_CONTEXT`: Input context
- `DAGSTER_PIPES_MESSAGES`: Output context

Create the following helper functions for reading the environment variables, decoding the data, and writing messages back to Dagster.

<CodeExample filePath="guides/non-python/pipes-javascript-utility.js" language="javascript" title="Utility functions to interface with Dagster Pipes." />

Both environment variables are base64 encoded, zip compressed JSON objects. Each JSON object contains a _path_ that indicate where to read or write data.

## Integrate the utility functions into your original script

With the utility functions to decode the Dagster Pipes environment variables, we can send additional parameters into the JavaScript process and output additional information into the asset materializations.

Update the `tensorflow/main.js` script to retrieve the model configuration from the Dagster context, and report an asset materialization back Dagster with model metadata.

<CodeExample filePath="guides/non-python/pipes-full-featured-javascript.js" language="javascript" title="Adding a new JavaScript entrypoint for Dagster Pipes." />

## Update your Dagster asset

Finally, update your Dagster asset to pass in the model information that's used by your script.

<CodeExample filePath="guides/non-python/pipes-asset-with-context.py" language="python" title="Asset using Dagster Pipes." />

## What's next?

From here, this example could be extended to support many JavaScript defined operations and many JavaScript based assets using different pairings of operations and configurations.
