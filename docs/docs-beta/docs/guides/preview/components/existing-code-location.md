---
title: 'Making an existing code location components-compatible'
sidebar_position: 300
unlisted: true
displayed_sidebar: 'components'
---

:::note
This guide is only relevant if you are starting from an _existing_ Dagster code location. This setup is unnecessary if you used `dg code-location generate` to create your code location.
:::

## Create a `components` directory

First, you'll want to create a directory to contain any new components you add to your code location. By convention, this directory is named `components`, and exists at the top level of your code location's Python module.

```bash
mkdir components
```

## Modify top-level definitions

`dagster-components` provides a utility to create a `Definitions` object from your components directory. Because you're working with an existing code location, you'll want to combine your existing definitions with the ones from your components directory.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You can manually construct a set of definitions for your components using `build_component_defs`, then merge them with your existing definitions using `Definitions.merge`. You point `build_components_defs` at the directory you just created that contains components.

<Tabs>
    <TabItem value='before' label='Before'>
        <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/definitions-before.py" language="python" />
    </TabItem>
    <TabItem value='after' label='After'>
        <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/definitions-after.py" language="python" />
    </TabItem>
</Tabs>

## Next steps

- Add a new component to your code location
- Create a new component type
