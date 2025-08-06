---
title: 'Dagster & Kubernetes jobs with components'
description: Execute Kubernetes jobs as assets with Dagster components
sidebar_position: 404
---

Dagster provides a ready-to-use `PipesK8sComponent` which can be used to execute Kubernetes jobs as assets in your Dagster project. This component runs your containerized workloads in Kubernetes pods using Dagster Pipes, allowing you to leverage existing Docker images and Kubernetes configurations while benefiting from Dagster's orchestration and observability features. This guide will walk you through how to use the `PipesK8sComponent` to execute your Kubernetes jobs.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

Install the `dagster-k8s` package to access the Kubernetes components:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/2-install-dagster-k8s.txt" />

## 3. Scaffold a Kubernetes component

Now that you have a Dagster project, you can scaffold a Kubernetes component. You'll need to provide a name for your component. In this example, we'll create a component that will execute a Kubernetes job to process data and generate reports.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/3-scaffold-k8s-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/4-tree.txt" />

## 4. Create your container image

Build a Docker image that contains your data processing code. **You can use any existing Docker image** - Dagster will orchestrate it in Kubernetes without requiring changes to your container. For this example, we'll create a simple data processing container:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/5-dockerfile"
  title="my-project/src/my_project/defs/process_data/Dockerfile"
  language="dockerfile"
/>

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/6-process-data-script.py"
  title="my-project/src/my_project/defs/process_data/process_data.py"
  language="python"
/>

Build and push your image:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/7-build-image.txt" />

## 5. Configure your component

Update your `defs.yaml` file to specify the container image and define the assets that will be created. You can also specify properties for the asset in Dagster, such as a group name and description:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/8-customized-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

You can run `dg list defs` to see the asset corresponding to your component:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/9-list-defs.txt" />
</WideContent>

## 6. Launch your assets

Once your component is configured, you can launch your assets to execute the Kubernetes jobs:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/10-launch.txt" />

Navigate to the Dagster UI and you'll see your assets. Click on the asset and then "Materialize" to execute your Kubernetes job. The job will run in your cluster, and you'll be able to see the logs and metadata in the Dagster UI.

## 7. Advanced configuration

### Log metadata inside Kubernetes jobs

For more advanced use cases, you can use [Dagster Pipes](/guides/build/external-pipelines/) to pass metadata from your Kubernetes job back to Dagster. This allows you to provide rich information about your assets directly in the Dagster UI:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/11-advanced-pipes-script.py"
  title="my-project/src/my_project/defs/process_data/process_data_with_pipes.py"
  language="python"
/>

With Dagster Pipes, you can:

- **Log structured information**: Use `context.log.info()` to send logs directly to Dagster
- **Report asset metadata**: Use `context.report_asset_materialization()` to attach rich metadata that appears in the Dagster UI
- **Handle errors**: Exception information is automatically captured and reported to Dagster

### Orchestrate multiple Kubernetes jobs

You can define multiple Kubernetes components in a single `defs.yaml` file using the `---` separator syntax. This allows you to run different container images for different assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/12-multiple-jobs-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

Each component instance runs independently and can execute different container images. This approach is useful when you have multiple related data processing tasks that should be organized together but run separately.

### Set up dependencies

You can specify dependencies between assets from different Kubernetes jobs. Using the multiple jobs example above, you can make one job depend on another:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/13-dependencies-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

### Automate Kubernetes jobs

You can configure when assets should be automatically materialized using automation conditions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/14-automation-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

### Configure Kubernetes resources

You can specify resource requirements, environment variables, and other Kubernetes configuration:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/15-resource-config-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

### Use custom namespace and pod specifications

For advanced Kubernetes configurations, you can specify custom namespaces and pod specifications:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/k8s-component/16-advanced-k8s-component.yaml"
  title="my-project/src/my_project/defs/process_data/defs.yaml"
  language="yaml"
/>

## Best practices

- **Start simple**: Begin with basic container images that log output for basic orchestration needs.
- **Use Dagster Pipes for rich metadata**: Leverage `open_dagster_pipes()` context manager to stream structured asset materialization events back to Dagster.
- **Keep containers focused**: Each container should have a clear, single responsibility, and offload complex dependencies to Dagster to benefit from native observability like lineage tracking and asset metadata.
- **Manage resources**: Always specify appropriate CPU and memory limits to prevent resource contention in your cluster.
- **Use proper RBAC**: Ensure your Kubernetes service account has the necessary permissions to create and manage jobs and pods.