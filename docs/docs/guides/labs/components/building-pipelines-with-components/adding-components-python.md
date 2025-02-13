---
title: 'Adding Components to your project with Python'
sidebar_position: 300
---

In some cases, you may want to add a Component to your project with Python rather than a `component.yaml` file.

:::note Prerequisites

Before adding a Component with Python, you must either [create a project with Components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components) or [migrate an existing code location to Components](/guides/labs/components/migrating-to-components/migrating-code-locations).

:::

1. First, create a new subdirectory in your `components/` directory to contain the Component definition.
2. In the subdirectory, create a `component.py` file to define your component instance. In this file, you will define a single `@component`-decorated function that instantiates the component type that you're interested in:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/python-components/component.py" language="python" />

This function just needs to return an instance of your desired Component type. In the example above, we've used this functionality to customize the `translator` argument of the `DbtProjectComponent` class.
