---
title: 'Testing component types'
sidebar_position: 700
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

Components are designed for unit testing much like the rest of the Dagster framework. It comes with utilities that are useful for doing this.

At their core, components are factories that produce definitions such as assets,
asset checks, sensors, and so forth. Those factories are parameterized with either yaml or Python objects.

## A Simple Asset

Imagine you have authored the following custom component:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/testing-components-types/1-simple-component.py"
  language="python"
  title="my_project/src/my_project/lib/simple_component.py"
/>

You can just directly create the component in Python and pass it
to `component_defs`, which is a convenience function that creates its corresponding `Definitions` object.

With that `Definitions` object you can test against it like any
other definition.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/testing-components-types/2-test-simple-component.py"
  language="python"
  title="my_project/tests/test_simple_component.py"
/>

## Resources

Users often use resources to separate I/O and environmental concerns from business logic.


<CodeExample
  path="docs_snippets/docs_snippets/guides/components/testing-components-types/3-component-with-resources.py"
  language="python"
  title="my_project/src/my_project/lib/component_with_resources.py"
/>

In this case you can parametrize `component_defs` with the resources you to bind to all the definitinos you are loading:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/testing-components-types/4-test-component-with-resources.py"
  language="python"
  title="my_project/tests/test_component_with_resources.py"
/>