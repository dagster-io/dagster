---
title: 'Adding components to your project with Python'
sidebar_position: 300
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

In some cases, you may want to add a component to your project with Python rather than a `component.yaml` file.

:::note Prerequisites

Before adding a component with Python, you must either [create a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components) or [migrate an existing project to `dg`](/guides/labs/dg/incrementally-adopting-dg/migrating-project).

:::

1. First, create a new subdirectory in your `components/` directory to contain the component definition.
2. In the subdirectory, create a `component.py` file to define your component instance. In this file, you will define a single `@component`-decorated function that instantiates the component type that you're interested in:

<CodeExample path="docs_snippets/docs_snippets/guides/components/python-components/component.py" language="python" />

This function needs to return an instance of your desired component type. In the example above, we've used this functionality to customize the `translator` argument of the `DbtProjectcomponent` class.
