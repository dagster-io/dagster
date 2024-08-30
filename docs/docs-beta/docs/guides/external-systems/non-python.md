---
title: "Running non-Python languages"
sidebar_position: 60
---

Dagster is written in Python, but that doesn't mean it's limited to running Python to materialize assets. With Pipes, you can run code in other languages and send information back to Dagster. This guide covers how to run JavaScript with Dagster using Pipes, however, the same principle will apply to other languages.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- A basic understanding of JavaScript
</details>

# Define a JavaScript-based asset

We will demonstrate running JavaScript code using Dagster Pipes. In this example, the `train_model` function loads a CSV and trains a sequential model using the Tensorflow library.

<CodeExample filePath="guides/automation/pipes-contrived-javascript.py" language="javascript" title="A simple Tensorflow function." />

With an `@asset` definition in Dagster, you can now invoke your JavaScript function from Dagster.

<CodeExample filePath="guides/automation/pipes-asset.py" language="python" title="Asset using Dagster Pipes." />

If the command passed to Dagster Pipes (`node tensorflow/main.js`) exits successfully, then an asset materialization result will be created implicitly for the asset defined here. Additionally, the stdout/stderr will be collected into the asset logs. Dagster Pipes supports passing parameters into Pipes and allowing Pipes processes to more explicitly define the asset materialization event.

# Add JavaScript utility functions to interface with Dagster Pipes

Dagster Pipes follows a similar design to Unix pipes, hence the name. The `PipesSubprocessClient` is responsible for running external processes and setting up input/output files. The asset defined here is materialized using the `PipesSubprocessClient` running a Node.js file containing the `train_model` function.

The `PipesSubprocessClient` calls the child process with two environment variables defined, each containing a path to a file. One for input and one for output.
- DAGSTER_PIPES_CONTEXT: Input context
- DAGSTER_PIPES_MESSAGES: Output context

<CodeExample filePath="guides/automation/pipes-javascript-utility.py" language="javascript" title="Utility functions to interface with Dagster Pipes." />

Both environment variables are base64, zip compressed JSON objects with a "path" key. These functions decode these environment variables and access the files to hook up our JavaScript function to Dagster.

# Create a JavaScript interface for Dagster to invoke

With the utility functions to decode the Dagster Pipes environment variables, a JavaScript function is needed to translate the Dagster Pipes context into a function evocation.

<CodeExample filePath="guides/automation/pipes-full-featured-javascript.js" language="javascript" title="Adding a new JavaScript entrypoint for Dagster Pipes." />

`run_operation` creates an API between Dagster and the Node.js file:
- Input: The `operation_name` to invoke and a `config` for the operation.
- Output: Reports an asset materialization with metadata about the model.

# Call the JavaScript interface using Dagster Pipes

Updating the asset definition with the additional information in the `extras` field allows the asset to work end to end.

<CodeExample filePath="guides/automation/pipes-asset-with-context.py" language="python" title="Asset using Dagster Pipes." />

# What's next?

From here, this example could be extended to support many JavaScript defined operations and many JavaScript based assets using different pairings of operations and configurations.
