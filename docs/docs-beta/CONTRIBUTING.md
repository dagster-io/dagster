# Contributing

## Migration from legacy docs

There are some features in the previous docs that require changes to be made to work in the new Docusaurus-based documentation site.

### Images

Before:

```
<Image
  alt="Highlighted Redeploy option in the dropdown menu next to a code location in Dagster+"
  src="/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png"
  width={1920}
  height={284}
/>
```

After:

```
<ThemedImage
  alt="Highlighted Redeploy option in the dropdown menu next to a code location in Dagster+"
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
    dark: '/images/dagster-cloud/developing-testing/code-locations/redeploy-code-location.png',
  }}
/>
```

### Notes

Before:

```
<Note>This guide is applicable to Dagster+.</Note>
```

After:

```
:::note
This guide is applicable to Dagster+
:::
```

### Tabs

Before:

```
<TabGroup>
  <TabItem name="Amazon ECS">
  ...
  </TabItem>
</TabGroup>
```

After:

```
<Tabs>
  <TabItem value="Amazon ECS">
  ...
  </TabItem>
</Tabs>
```

### Header boundaries

Previously, horizontal rules had to be defined between each level-two header: `---`.

This is no longer required, as the horizontal rule has been included in the CSS rules.

### Reference tables

Before:

```
<ReferenceTable>
  <ReferenceTableItem propertyName="container_context.ecs.env_vars">
    A list of keys or key-value pairs to include in the task. If a value is not
    specified, the value will be pulled from the agent task.
    <br />
    In the example above, <code>FOO_ENV_VAR</code> will be set to{" "}
    <code>foo_value</code> and <code>BAR_ENV_VAR</code> will be set to whatever
    value it has in the agent task.
  </ReferenceTableItem>
</ReferenceTable>
```

After:

_There is not a replacement at this point in time..._

### Whitespace via `{" "}`

Forcing empty space using the `{" "}` interpolation is not supported, and must be removed.
