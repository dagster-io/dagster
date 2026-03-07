---
title: 'Define a Dagster asset that invokes subprocess'
description: 'Learn how to create a Dagster asset that invokes a subprocess that executes external code.'
sidebar_position: 100
---

:::note

This is part one of the [Using Dagster Pipes](/integrations/external-pipelines/using-dagster-pipes) tutorial. If you are looking for how to modify your existing code that is already being orchestrated by Dagster, you can jump to part 2, [Modify external code](/integrations/external-pipelines/using-dagster-pipes/modify-external-code).

:::note

In this part of the tutorial, you'll create a Dagster asset that, in its execution function, opens a Dagster pipes session and invokes a subprocess that executes some external code.

:::

## Step 1: Create a Dagster project

First we will create a new Dagster project:

```bash
uvx create-dagster@latest project external_pipeline
```

## Step 2: Scaffold and define the asset

Next, we can scaffold the asset file:

```bash
dg scaffold defs dagster.assets dagster_code.py
```

Next, you’ll define the asset. Copy and paste the following into the file `src/external_pipeline/defs/dagster_code.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/part_1/dagster_code.py"
  startAfter="start_asset_marker"
  endBefore="end_asset_marker"
  title="src/external_pipeline/defs/dagster_code.py"
/>

## Step 3: Add external code file

Before we define our asset code, we will add a standalone Python script named `external_code.py` within the directory we just scaffolded (`src/external_pipeline/defs/`). Later, we will invoke a subprocess that executes this external code from the asset using the `pipes_subprocess_client resource`. The external code looks like the following:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/part_1/external_code.py"
  startAfter="start_external_code"
  endBefore="end_external_code"
  title="src/external_pipeline/defs/external_code.py"
/>

Here’s what we did in this code:

- Created an asset named `subprocess_asset`
- Provided <PyObject section="execution" module="dagster" object="AssetExecutionContext" /> as the `context` argument to the asset. This object provides system information such as resources, config, and logging. We’ll come back to this a bit later in this section.
- Specified a resource for the asset to use, `PipesSubprocessClient`. We’ll also come back to this in a little bit.
- Declared a command list `cmd` to run the external script. In the list:
  - First, found the path to the Python executable on the system using `shutil.which("python")`.
  - Then, provided the file path to the file that we want to execute. In this case, it’s the `external_code.py` file that you created earlier.

### Step 4: Invoke the external code from the asset

Next, invoke a subprocess that executes the external code from the asset using the `pipes_subprocess_client` resource:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/part_1/dagster_code.py"
  startAfter="start_asset_marker"
  endBefore="end_asset_marker"
  title="src/external_pipeline/defs/dagster_code.py"
/>

Let’s take a look at what this code does:

- The `PipesSubprocessClient` resource used by the asset exposes a `run` method.
- When the asset is executed, this method will synchronously execute the subprocess in in a pipes session, and it will return a `PipesClientCompletedInvocation` object.
- This object contains a `get_materialize_result` method, which you can use to access the <PyObject section="assets" module="dagster" object="MaterializeResult" /> event reported by the subprocess. We'll talk about how to report events from the subprocess in the next section.
- Lastly, return the result of the subprocess.

## Step 5: Define a Definitions object

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

To make the subprocess resource loadable and accessible, such as the CLI, UI, and Dagster+, you’ll create a function with the <PyObject section="definitions" module="dagster" object="Definitions" decorator />.

Copy and paste the following to the bottom of `src/external_pipeline/defs/resources.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/resources.py"
  title="src/external_pipeline/defs/resources.py"
/>

At this point, `dagster_code.py` should look like the following:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/subprocess/part_1/dagster_code_finished.py"
  title="src/external_pipeline/defs/dagster_code.py"
/>

## Step 6: Run the subprocess from the Dagster UI

In this step, you’ll execute the subprocess asset you created in earlier steps from the Dagster UI.

1. In a new command line session, run the following to start the UI:

   ```bash
   dg dev
   ```

2. Navigate to [http://localhost:3000](http://localhost:3000), where you should see the UI:

   ![Asset in the UI](/images/guides/build/external-pipelines/subprocess/part-1-step-3-2-asset.png)

3. Click **Materialize** located in the top right to run your code:

   ![Materialize asset](/images/guides/build/external-pipelines/subprocess/part-1-step-3-3-materialize.png)

4. Navigate to the **Run details** page, where you should see the logs for the run:

   ![Logs in the run details page](/images/guides/build/external-pipelines/subprocess/part-1-step-3-4-logs.png)

5. In `external_code.py`, we have a `print` statement that outputs to `stdout`. Dagster will display these in the UI's raw compute log view. To see the `stdout` log, toggle the log section to **stdout**:

   ![Raw compute logs in the run details page](/images/guides/build/external-pipelines/subprocess/part-1-step-3-5-stdout.png)

## What's next?

At this point, you've created a Dagster asset that invokes an external Python script, launched the code in a subprocess, and viewed the result in Dagster UI. Next, you'll learn how to [modify your external code to work with Dagster Pipes](/integrations/external-pipelines/using-dagster-pipes/modify-external-code) to send information back to Dagster.
