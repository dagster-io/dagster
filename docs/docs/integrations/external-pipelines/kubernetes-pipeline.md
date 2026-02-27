---
title: Kubernetes pipelines
description: 'Learn to integrate Dagster Pipes with Kubernetes to launch external code from Dagster assets.'
sidebar_position: 60
---

import ScaffoldProject from '@site/docs/partials/\_ScaffoldProject.md';

:::note

This article focuses on using an out-of-the-box Kubernetes resource. For further customization, use the [`open_pipes_session`](/integrations/external-pipelines/dagster-pipes-details-and-customization) approach instead.

:::

This article covers how to use [Dagster Pipes](/integrations/external-pipelines) with Dagster's [Kubernetes integration](/integrations/libraries/k8s) to launch Kubernetes pods and execute external code.

Pipes allows your code to interact with Dagster outside of a full Dagster environment. Instead, the environment only needs to contain [`dagster-pipes`](https://pypi.org/project/dagster-pipes), a single-file Python package with no dependencies that can be installed from PyPI or easily vendored. `dagster-pipes` handles streaming `stdout`/`stderr` and Dagster events back to the orchestration process.

:::note

You can omit the `dagster-pipes` dependency entirely if you do not wish to use the features like log streaming or event emission&mdash;pipes can still orchestrate these Kubernetes jobs.

:::

## Prerequisites

To run the examples, you'll need to:

- Create a new Dagster project:
  <ScaffoldProject />
- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-k8s
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-k8s
         ```

   </TabItem>
</Tabs>

- A Kubernetes cluster. This can be an existing cluster, or, if you're working locally, you can use [kind](https://kind.sigs.k8s.io) or [Docker Desktop](https://docs.docker.com/desktop/kubernetes).

## Step 1: Define the external Kubernetes code container

In this step, you'll create a Kubernetes container image that runs some code that uses `dagster-pipes`.

### Step 1.1: Write a Python script

First, you'll write a Python script that uses `dagster-pipes` and is executed in a container via Kubernetes:

```python
# my_python_script.py

from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    # Stream log message back to Dagster
    pipes.log.info(f"Using some_parameter value: {pipes.get_extra('some_parameter')}")

    # ... your code that computes and persists the asset

    pipes.report_asset_materialization(
        metadata={
            "some_metric": {"raw_value": 2, "type": "int"}
        },
        data_version="alpha",
    )
```

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

Let's review what this code does:

- Imports <PyObject section="libraries" integration="pipes" object="open_dagster_pipes" module="dagster_pipes" /> from `dagster_pipes`

- **Initializes the Dagster Pipes context (<PyObject section="libraries" integration="pipes" object="open_dagster_pipes" module="dagster_pipes" />), which yields an instance of <PyObject section="libraries" integration="pipes" object="PipesContext" module="dagster_pipes" /> called `pipes`.**

  We're using the default context loader (<PyObject section="libraries" integration="pipes" object="PipesDefaultContextLoader" module="dagster_pipes" />) and message writer (<PyObject section="libraries" integration="pipes" object="PipesDefaultMessageWriter" module="dagster_pipes" />) in this example. These objects establish communication between the orchestration and external process. On the orchestration end, these match a corresponding `PipesContextInjector` and `PipesMessageReader`, which are instantiated inside the <PyObject section="libraries" integration="k8s" module="dagster_k8s" object="PipesK8sClient" />.

- **Inside the body of the context manager (<PyObject section="libraries" integration="pipes" object="open_dagster_pipes" module="dagster_pipes" />), retrieve a log and report an asset materialization.** These calls use the temporary communications channels established by <PyObject section="libraries" integration="pipes" object="PipesDefaultContextLoader" module="dagster_pipes" /> and <PyObject section="libraries" integration="pipes" object="PipesDefaultMessageWriter" module="dagster_pipes" />. To see the full range of what you can do with the <PyObject section="libraries" integration="pipes" object="PipesContext" module="dagster_pipes" />, see the API docs or the general [Pipes documentation](/integrations/external-pipelines).

At this point you can execute the rest of your Kubernetes code as normal, invoking various <PyObject section="libraries" integration="pipes" object="PipesContext" module="dagster_pipes" /> APIs as needed.

### Step 1.2: Define and build the container image

Next, you'll package the script into a container image using a `Dockerfile`. For example:

```dockerfile
FROM python:3.10-slim

RUN pip install dagster-pipes

COPY my_python_script.py .

ENTRYPOINT [ "python","my_python_script.py" ]
```

Then, build the image:

```shell
docker build -t pipes-example:v1 .
```

**Note**: Depending on the Kubernetes setup you're using, you may need to upload the container image to a registry or otherwise make it available to the cluster. For example: `kind load docker-image pipes-example:v1`

---

## Step 2: Create the Dagster objects

In this step, you'll create a Dagster asset that, when materialized, opens a Dagster pipes session and spins up a Kubernetes pod to execute the container created in the previous step.

### Step 2.1: Define the Dagster asset

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

In your Dagster project, create a file named `assets.py` and paste in the following code:

```python
import dagster as dg
from dagster_k8s import PipesK8sClient


@dg.asset
def k8s_pipes_asset(context: dg.AssetExecutionContext, k8s_pipes_client: PipesK8sClient):
  return k8s_pipes_client.run(
      context=context,
      image="pipes-example:v1",
      extras={
            "some_parameter": 1
      }
  ).get_materialize_result()
```

Here's what we did in this example:

- Created an asset named `k8s_pipes_asset`

- Provided <PyObject section="execution" module="dagster" object="AssetExecutionContext" /> as the `context` argument to the asset. This object provides access to system APIs such as resources, config, and logging.

- Specified a resource for the asset to use, <PyObject section="libraries" integration="k8s" module="dagster_k8s" object="PipesK8sClient" />, which is a pre-built Dagster resource that allows you to quickly get Pipes working with Kubernetes.

  We also specified the following for the resource:

  - `context` - The asset's `context` (<PyObject section="execution" module="dagster" object="AssetExecutionContext" />) data
  - `image` - The Kubernetes image we created in [Step 1](#step-1-define-the-external-kubernetes-code-container)

  These arguments are passed to the `run` method of <PyObject section="libraries" integration="k8s" module="dagster_k8s" object="PipesK8sClient" />, which submits the provided cluster information to the Kubernetes API and then runs the specified `image`.

- Returned a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object representing the result of execution. This is obtained by calling `get_materialize_result` on the `PipesClientCompletedInvocation` object returned by `run` after the execution in Kubernetes has completed.
  {/* TODO replace `PipesClientCompletedInvocation` with <PyObject section="pipes" module="dagster" object="PipesClientCompletedInvocation" /> */}

:::note

Depending on your Kubernetes setup, there may be a few additional things you need to do:

- **If the default behavior doesn't target the correct cluster**, supply the `load_incluster_config`, `kubeconfig_file`, and `kube_context` arguments on <PyObject section="libraries" integration="k8s" module="dagster_k8s" object="PipesK8sClient" />
- **If you need to alter default spec behaviors**, use arguments on `PipesK8sClient.run` such as `base_pod_spec`.

:::

### Step 2.2: Create Dagster Definitions

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

Next, you'll add the asset and Kubernetes resource to your project's code location via the <PyObject section="definitions" module="dagster" object="Definitions" /> object. This makes the resource available to [other Dagster definitions in the project](/guides/build/projects).

Copy and paste the following to the bottom of `resources.py`:

```python
@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "k8s_pipes_client": PipesK8sClient(),
        }
    )
```

At this point, the files should look like the following:

```python title="src/<project_name>/defs/assets.py"
import dagster as dg
from dagster_k8s import PipesK8sClient


@dg.asset
def k8s_pipes_asset(context: dg.AssetExecutionContext, k8s_pipes_client: PipesK8sClient):
  return k8s_pipes_client.run(
      context=context,
      image="pipes-example:v1",
      extras={
            "some_parameter": 1
      }
  ).get_materialize_result()
```

```python title="src/<project_name>/defs/resources.py"
import dagster as dg
from dagster_k8s import PipesK8sClient


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "k8s_pipes_client": PipesK8sClient(),
        }
    )
```

## Step 3: Launch the Kubernetes container from the Dagster UI

In this step, you'll run the Kubernetes container you defined in [Step 1](#step-1-define-the-external-kubernetes-code-container) from the Dagster UI.

1. In a new command line session, run the following to start the UI:

   ```python
   dg dev
   ```

2. Navigate to [localhost:3000](http://localhost:3000), where you should see the UI.

3. Click **Materialize** near the top right corner of the page, then click **View** on the **Launched Run** popup. Wait for the run to complete, and the event log should look like this:

   ![Event log for Kubernetes run](/images/guides/build/external-pipelines/kubernetes/run.png)
