---
title: 'Adding components to your project with Python'
sidebar_position: 300
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

In some cases, you may want to add a component to your project with Python rather than a `component.yaml` file.

:::note Prerequisites

Before adding a component with Python, you must either [create a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components) or [migrate an existing project to components](/guides/labs/components/incrementally-adopting-components/existing-project).

:::

1. First, create a new subdirectory in your `components/` directory to contain the component definition.
2. In the subdirectory, create a `component.py` file to define your component instance. In this file, you will define a single `@component`-decorated function that instantiates the component type that you're interested in:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/python-components/component.py" language="python" />

This function needs to return an instance of your desired component type. In the example above, we've used this functionality to customize the `translator` argument of the `DbtProjectcomponent` class.
