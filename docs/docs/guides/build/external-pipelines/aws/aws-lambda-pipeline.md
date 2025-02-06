---
title: Build pipelines with AWS Lambda
description: "Learn to integrate Dagster Pipes with AWS Lambda to launch external code from Dagster assets."
sidebar_position: 600
---

:::note

This article focuses on using an out-of-the-box Amazon Web Services (AWS) Lambda resource. For further customization, use the [`open_pipes_session`](/guides/build/external-pipelines/dagster-pipes-details-and-customization) instead.

:::

This article covers how to use [Dagster Pipes](/guides/build/external-pipelines/) with Dagster's AWS Lambda integration to invoke a Lambda function and execute external code.

Dagster Pipes allows your code to interact with Dagster outside of a full Dagster environment. The environment only needs to contain `dagster-pipes`, a single-file Python package with no dependencies that can be installed from PyPI or easily vendored. `dagster-pipes` handles streaming `stdout`/`stderr` and Dagster events back to the orchestration process.

## Prerequisites

<details>
    <summary>Prerequisites</summary>

    - **In the Dagster environment**, you'll need to:

    - Install the following packages:

        ```shell
        pip install dagster dagster-webserver dagster-aws
        ```

        Refer to the [Dagster installation guide](/getting-started/installation) for more info.

    - **Configure AWS authentication credentials.** If you don't have this set up already, refer to the [boto3 quickstart](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).

    - **In AWS**, you'll need:

    - An existing AWS account with access to Lambda
    - Permissions that allow you to create and modify Lambda functions

</details>

## Step 1: Create a Lambda function

First, you'll create a Lambda function using the AWS UI.

### Step 1.1: Create the function in the AWS UI

For simplicity we're demonstrating this step using the UI, but you can also do this programmatically. Refer to the [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/API_CreateFunction.html) for more info.

1. Sign into the AWS console.
2. Navigate to Lambda.
3. On the Lambda page, click **Create function**.
4. On the **Create function** page, fill in the following in **Basic information**:
   - **Function name** - Enter a name for the function. For example: `dagster_pipes_function`
   - **Runtime** - Select **Python 3.10**
5. Click **Create function**.

After the function is created, you'll be redirected to a page like the following:

![The lambda function details page in the AWS UI](/images/guides/build/external-pipelines/aws-lambda/aws-lambda-function-details.png)

### Step 1.2: Add a dagster-pipes file

Next, you'll add `dagster-pipes` to the function.

:::note

For simplicity, we're going to copy the contents of the single Dagster Pipes file and add it to the function. While this means we won't automatically receive future updates, Dagster aims to only make changes that are backwards-compatible. This means we'll have to periodically check for updates, but it's unlikely we'll have to update our code in any significant way.

:::

1. In the **Code source** section of the page, add a new file. This can be accomplished with **File > New file** or by clicking the green **+** icon next to the open `lambda_function` tab:

    ![Highlighted New file option in a menu of the Code source section on the Lambda function details page](/images/guides/build/external-pipelines/aws-lambda/aws-lambda-create-new-file.png)

2. **In a new browser tab**, navigate to the following URL:

   ```shell
   https://raw.githubusercontent.com/dagster-io/dagster/master/python_modules/dagster-pipes/dagster_pipes/__init__.py
   ```

3. Copy the contents of `__init__.py` into the new file you created in AWS. **Note**: We recommend adding the source link and the date you copied the contents to the top of the file as comments:

    ![The copied contents of the Dagster Pipes file into a file in the AWS UI](/images/guides/build/external-pipelines/aws-lambda/aws-lambda-add-dagster-pipes.png)

4. Save the file as `dagster_pipes.py`.

### Step 1.3: Add the code to execute to the function

In this step, you'll add the code you want to execute to the function. Create another file in the AWS UI - or use the default `lambda_function.py` file created by the function - and paste in the following code:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/lambda/lambda_function.py" />

:::tip

The metadata format shown above (`{"raw_value": value, "type": type}`) is part of Dagster Pipes' special syntax for specifying rich Dagster metadata. For a complete reference of all supported metadata types and their formats, see the [Dagster Pipes metadata reference](/guides/build/external-pipelines/using-dagster-pipes/reference#passing-rich-metadata-to-dagster).

:::

Let's review what this code does:

- Imports [`PipesMappingParamsLoader`](/api/python-api/libraries/dagster-pipes#params-loaders) and <PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" /> from `dagster_pipes`

- **Defines a [Lambda function handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html), which is a method in function code that processes events**. This method accepts `event` and `context` arguments, which map to the `event` payload and `context` we'll define in our Dagster asset.

- **Initializes the Dagster Pipes context (<PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" />), which yields an instance of <PyObject section="libraries" object="PipesContext" module="dagster_pipes" /> called `pipes`.**

  On the orchestration side - which we'll discuss in the next section - we'll set up a Dagster asset that uses the <PyObject section="libraries" module="dagster_aws" object="pipes.PipesLambdaClient" /> to inject information needed for Pipes in an `event` payload. In this code on the AWS Lambda side, we're passing this payload to [`PipesMappingParamsLoader`](/api/python-api/libraries/dagster-pipes#params-loaders) and using it in <PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" />.

  We're using the default context loader (<PyObject section="libraries" object="PipesDefaultContextLoader" module="dagster_pipes" />) and message writer (<PyObject section="libraries" object="PipesDefaultMessageWriter" module="dagster_pipes" />) in this example. These objects establish communication between the orchestration and external process. On the orchestration end, these match a corresponding `PipesLambdaEventContextInjector` and `PipesLambdaLogsMessageReader`, which are instantiated inside the <PyObject section="libraries" module="dagster_aws" object="pipes.PipesLambdaClient" />.

- **Inside the body of the context manager (<PyObject section="libraries" object="open_dagster_pipes" module="dagster_pipes" />), retrieve a log and report an asset materialization.** These calls use the temporary communications channels established by <PyObject section="libraries" object="PipesDefaultContextLoader" module="dagster_pipes" /> and <PyObject section="libraries" object="PipesDefaultMessageWriter" module="dagster_pipes" />. To see the full range of what you can do with the <PyObject section="libraries" object="PipesContext" module="dagster_pipes" />, see the [API docs](/api/python-api/pipes) or the general [Pipes documentation](/guides/build/external-pipelines).

At this point you can execute the rest of your AWS Lambda code as normal, invoking various <PyObject section="libraries" object="PipesContext" module="dagster_pipes" /> APIs as needed.

### Step 1.3: Deploy the function

When finished, click the **Deploy** button to update and deploy the function.

## Step 2: Create the Dagster objects

In this step, you'll create a Dagster asset that, when materialized, opens a Dagster pipes session and invokes the Lambda function you created in [Step 1](#step-1-create-a-lambda-function).

### Step 2.1: Define the Dagster asset

In your Dagster project, create a file named `dagster_lambda_pipes.py` and paste in the following code:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/lambda/dagster_code.py" startAfter="start_asset_marker" endBefore="end_asset_marker" />

Here's what we did in this example:

- Created an asset named `lambda_pipes_asset`

- Provided `AssetExecutionContext` as the `context` argument to the asset. This object provides access to system APIs such as resources, config, and logging.

- Specified a resource for the asset to use, <PyObject section="libraries" module="dagster_aws" object="pipes.PipesLambdaClient" />, which is a pre-built Dagster resource that allows you to quickly get Pipes working with AWS Lambda.

  We also specified the following for the resource:

  - `context` - The asset's `context` (`AssetExecutionContext`) data
  - `function_name` - The name or ARN of the function to invoke. This info can be found on the function's details page in AWS. In our example, the function is named `dagster_pipes_function`
  - `event` - A JSON-serializable object containing data to pass as input to the Lambda function

  This argument is passed to the `run` method of <PyObject section="libraries" module="dagster_aws" object="pipes.PipesLambdaClient" />, which submits the provided information to the [boto `invoke` API](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/invoke.html) and then invokes the specified function (`function_name`).

- Returned a <PyObject section="assets" module="dagster" object="MaterializeResult" /> object representing the result of execution. This is obtained by calling `get_materialize_result` on the `PipesClientCompletedInvocation` object returned by `run` after the execution in AWS Lambda has completed.
{/* TODO replace `PipesClientCompletedInvocation` with <PyObject section="libraries" module="pipes" object="dagster.PipesClientCompletedInvocation" /> */}

### Step 2.2: Create Dagster Definitions

Next, you'll add the asset and AWS Lambda resource to your project's code location via the <PyObject section="definitions" module="dagster" object="Definitions" /> object. This makes the resource available to [other Dagster definitions in the project](/guides/deploy/code-locations).

Copy and paste the following to the bottom of `dagster_lambda_pipes.py`:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/dagster_pipes/lambda/dagster_code.py" startAfter="start_definitions_marker" endBefore="end_definitions_marker" />

Sometimes, you may want to transition data pipelines between development and production environments without minimal code changes. To do so, you can use the [Resources](/guides/build/external-resources) system to vary the Pipes clients based on different deployments. For example, you can specify different configured `boto3` clients. Or, you may handle the switch by swapping underlying AWS environment variables between deployments. For more info, check out detailed guides in [Transitioning Data Pipelines from Development to Production](/guides/deploy/dev-to-prod) and [Testing against production with Dagster+ Branch Deployments](/dagster-plus/features/ci-cd/branch-deployments/testing).

## Step 3: Invoke the AWS Lambda function from the Dagster UI

In this step, you'll invoke the AWS Lambda function you defined in [Step 1](#step-1-create-a-lambda-function) from the Dagster UI.

1. In a new command line session, run the following to start the UI:

   ```python
   dagster dev -f dagster_lambda_pipes.py
   ```

2. Navigate to [localhost:3000](http://localhost:3000/), where you should see the UI.

3. Click **Materialize** near the top right corner of the page, then click **View** on the **Launched Run** popup. Wait for the run to complete, and the event log should look like this:

   ![Event log for AWS Lambda run](/images/guides/build/external-pipelines/aws-lambda/aws-lambda-dagster-ui.png)
