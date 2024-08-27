---
title: "Running non-Python languages"
sidebar_position: 60
---

Dagster is written in Python, but that doesn't mean it's limited to running Python to materialize assets. This guide covers how to run some JavaScript with Dagster using Pipes.

# Define your JavaScript function

Here's a contrived example of some JavaScript code to run using Dagster Pipes. `train_model` load some dataset and train a sequential model using tensorflow.

```javascript
import * as tf from '@tensorflow/tfjs';

async function train_model(config) {
  const { path_to_data, data_config, path_to_model } = config;
  const dataset = await tf.data.csv(path_to_data, data_config).map(({ xs, ys }) => {
    return {
      xs: tf.tensor2d(Object.values(xs), [Object.values(xs).length, 1]),
      ys: tf.tensor2d(Object.values(ys), [Object.values(ys).length, 1])
    };
  })
  .batch(100);

  const model = tf.sequential()
  model.add(tf.layers.dense({units: 1, inputShape: [1]}));
  model.compile({loss: 'meanSquaredError', optimizer: 'sgd'});

  await model.fitDataset(dataset, {epochs: 250})
  await model.save(path_to_model);
  model.summary();
  return model;
}
```

# Define your asset in Dagster

<CodeExample filePath="guides/automation/pipes-asset.py" language="python" title="Asset using Dagster Pipes." />

Dagster Pipes follows a similar design to Unix pipes, hence the name. The `PipesSubprocessClient` is responsible for running external processes and setting up input/output files. The asset defined here is materialized using the `PipesSubprocessClient` running a Node.js file containing the `train_model` function.

# Add JavaScript utility functions to access pipes

The `PipesSubprocessClient` calls the child process with two environment variables defined, each containing a path to a file. One for input and one for output.
- DAGSTER_PIPES_CONTEXT: Input context
- DAGSTER_PIPES_MESSAGES: Output context

Both environment variables are base64, zip compressed JSON objects with a "path" key. These functions decode these environment variables and access the files to hook up our JavaScript function to Dagster.

```javascript
import * as util from 'util';
import { promises as fs } from "fs";
import { inflate } from 'zlib';

const inflateAsync = util.promisify(inflate);

async function _decodeParam(value) {
  if (!value) {
    return null;
  }
  // Decode from base64 and unzip
  const decoded = Buffer.from(value, "base64");
  const decompressed = await inflateAsync(decoded);
  // Deserialize to JSON
  return JSON.parse(decompressed.toString("utf-8"));
}

async function getPipesContext() {
  // get the env var value for where the pipes context is stored
  const encodedPipesContextParam = process.env.DAGSTER_PIPES_CONTEXT;
  // decove the value to get the input file path
  const decodedPipesContextParam = await _decodeParam(encodedPipesContextParam);
  if (!decodedPipesContextParam) {
    return null;
  }
  return await fs.readFile(decodedPipesContextParam.path, "utf-8")
    .then((data) => JSON.parse(data));
}

async function setPipesMessages(message) {
  // get the env var value for where the pipes message is stored
  const encodedPipesMessagesParam = process.env.DAGSTER_PIPES_MESSAGES;
  // decode the value to get the output file path
  const decodedPipesMessagesParam = await _decodeParam(encodedPipesMessagesParam);
  if (!decodedPipesMessagesParam) {
    return null;
  }
  const path = decodedPipesMessagesParam.path;
  await fs.appendFile(path, JSON.stringify(message) + "\n");
}
```

# Create an API for Dagster to invoke

With the utility functions to decode the Dagster Pipes environment variables, a JavaScript function is needed to translate the Dagster Pipes context into a function evocation.

```javascript
const ALL_OPERATIONS = {
  train_model
}

async function run_operation() {
  const { asset_keys, extras: { operation_name, config } } = await getPipesContext()
  if (!(operation_name in ALL_OPERATIONS)) {
    setPipesMessages({ error: `Operation ${operation_name} not found` });
    return;
  }
  const operation = ALL_OPERATIONS[operation_name];
  const model = await operation(config);
  await setPipesMessages({
    method: "report_asset_materialization",
    params: {
      asset_key: asset_keys[0],
      data_version: null,
      metadata: {
        metrics: model.metrics ? { raw_value: model.metrics, type: "text" } : undefined,
        loss: { raw_value: model.loss, type: "text" },
      },
    },
  });
  return 0;
}

run_operation().then((result) => {
  process.exit(result);
});
```

`run_operation` creates an API between Dagster and the Node.js file:
- Input: The `operation_name` to invoke and a `config` for the operation.
- Output: Reports an asset materialization with metadata about the model.

# Call the API using Dagster pipes

Updating the asset definition with the additional information in the `extras` field allows the asset to work end to end finally.

<CodeExample filePath="guides/automation/pipes-asset.py" language="python" title="Asset using Dagster Pipes." />

# What's next?

From here, this example could be extended to support many JavaScript defined operations and many JavaScript based assets using different pairings of operations and configurations.
