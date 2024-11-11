---
title: "Unit testing assets and ops"
sidebar_position: 30
sidebar_label: "Unit testing"
---

Unit testing is essential for ensuring that computations function as intended. In the context of data pipelines, this can be particularly challenging. However, Dagster streamlines the process by enabling direct invocation of computations with specified input values and mocked resources, making it easier to verify that data transformations behave as expected.

While unit tests can't fully replace integration tests or manual review, they can catch a variety of errors with a significantly faster feedback loop.

This guide covers how to write unit tests for assets and ops with a variety of different input requirements.

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need familiarity with:

- [Assets](/concepts/assets)
- [Ops and Jobs](/concepts/ops-jobs)
</details>

## Before you start

Before you begin implementing unit tests, note that:

- Testing individual assets or ops is generally recommended over unit testing entire jobs
- Unit testing isn't recommended in cases where most of the business logic is encoded in an external system, such as an asset which directly invokes an external Databricks job.

## Assets and ops without arguments \{#no-arguments}

The simplest assets and ops to test are those with no arguments. In these cases, you can directly invoke definitions.

<Tabs>
  <TabItem value="asset-no-argument" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-no-argument.py" language="python"/>
  </TabItem>
  <TabItem value="op-no-argument" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-no-argument.py" language="python"/>
  </TabItem>
</Tabs>

## Assets and ops with upstream dependencies \{#upstream-dependencies}

If an asset or op has an upstream dependency, you can directly pass a value for that dependency when invoking the definition.

<Tabs>
  <TabItem value="asset-upstream" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-dependency.py" language="python" />
  </TabItem>
  <TabItem value="op-upstream" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-dependency.py" language="python" />
  </TabItem>
</Tabs>

## Assets and ops with config \{#config}

If an asset or op uses config, you can construct an instance of the required config object and pass it in directly.

<Tabs>
  <TabItem value="asset-config" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-config.py" language="python" />
  </TabItem>
  <TabItem value="op-config" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-config.py" language="python" />
  </TabItem>
</Tabs>

## Assets and ops with resources \{#resources}

If an asset or op uses a resource, it can be useful to create a mock instance of the resource to avoid interacting with external services.

<Tabs>
  <TabItem value="asset-resource" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-resource.py" language="python" />
  </TabItem>
  <TabItem value="op-resource" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-resource.py" language="python" />
  </TabItem>
</Tabs>

## Assets and ops with context \{#context}

If an asset or op uses a `context` argument, you can use `build_asset_context()` or `build_op_context()` to construct a context object.

<Tabs>
  <TabItem value="asset-context" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-context.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-context.py" language="python" />
  </TabItem>
</Tabs>

## Assets and ops with multiple parameters \{#multiple-parameters}

If an asset or op has multiple parameters, it's recommended to use keyword arguments for clarity.

<Tabs>
  <TabItem value="asset-parameters" label="Assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-combo.py" language="python" />
  </TabItem>
  <TabItem value="op-parameters" label="Ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-combo.py" language="python" />
  </TabItem>
</Tabs>

## Next steps

- Learn more about assets in [Understanding Assets](/concepts/assets)
- Learn more about ops in [Understanding Ops](/concepts/ops-jobs)
- Learn more about resources in [Resources](/concepts/resources)