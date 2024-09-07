---
title: "Unit tests for assets and ops"
sidebar_position: 30
sidebar_label: "Unit testing"
---

Unit testing is an important tool for verifying that a computation works as intended.

While this is traditionally difficult in the context of data pipelines, Dagster helps simplify this process by allowing you to directly invoke your computations with specific input values and mocked resources to ensure that they transform data as expected.

Unit tests can't fully replace integration tests or manual review, but *are* capable of catching a large variety of errors with a significantly faster feedback loop.

This guide covers how to write unit tests for assets and ops with a variety of different input requirements.

:::info

Unit testing individual assets or ops is generally recommended over unit testing entire jobs.

:::

:::info

Unit testing isn't recommended in cases where most of the business logic is encoded in an external system, such as an asset which directly invokes an external Databricks job.

:::


<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
</details>


## Testing assets and ops with no arguments

The simplest assets and ops to test are those with no arguments. In these cases, you can directly invoke your definition.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-no-argument.py" language="python"/>
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-no-argument.py" language="python"/>
  </TabItem>
</Tabs>

## Testing assets and ops that have upstream dependencies

If your asset or op has an upstream dependency, then you can directly pass a value for that dependency when invoking your definition.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-dependency.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-dependency.py" language="python" />
  </TabItem>
</Tabs>

## Testing assets and ops with config

If your asset or op uses [config](/todo), you can construct an instance of the required config object and pass it in directly.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-config.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-config.py" language="python" />
  </TabItem>
</Tabs>

## Testing assets and ops with resources

If your asset or op uses a [resource](/concepts/resources), it can be useful to create a mock instance of that resource to avoid interacting with external services.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-resource.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-resource.py" language="python" />
  </TabItem>
</Tabs>

## Testing assets and ops with context

If your asset or op uses a context argument, you can use `build_asset_context()` or `build_op_context()` to construct a context object.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-context.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-context.py" language="python" />
  </TabItem>
</Tabs>

## Testing assets and ops with a combination of parameters

If your asset or op has multiple parameters, it's recommended to use keyword arguments for clarity.

<Tabs>
  <TabItem value="asset" label="Using assets" default>
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-combo.py" language="python" />
  </TabItem>
  <TabItem value="op" label="Using ops">
    <CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/op-combo.py" language="python" />
  </TabItem>
</Tabs>
## Next steps

- Learn more about assets in [Understanding Assets](/concepts/assets)
- Learn more about ops in [Understanding Ops](/concepts/ops-jobs)
- Learn more about config in [Config](/todo)
- Learn more about resources in [Resources](/concepts/resources)