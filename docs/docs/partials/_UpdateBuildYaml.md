In the `build.yaml` file, replace `build.registry` with the registry used by the [agent you created in step 1](#step-1-generate-a-dagster-agent-token).

For example:

<CodeExample
  path="docs_snippets/docs_snippets/dagster-plus/deployment/branch-deployments/build.yaml"
  language="yaml"
  title="build.yaml"
/>

:::note

In older deployments, you may have a `dagster_cloud.yaml` file instead of a `build.yaml` file.

:::
