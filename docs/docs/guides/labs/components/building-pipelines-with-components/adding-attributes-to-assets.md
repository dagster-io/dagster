---
description: Within a Dagster dg-driven defs project layout, you can apply attribute transformations at any point in the directory structure.
sidebar_position: 400
title: Adding attributes to assets in a subdirectory
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

Attaching and modifying meta information on definitions such as assets is important in Dagster projects. You want to have groups, teams, owners, kinds, tags, and metadata set correctly to organize definitions and ensure that other tools and processes that rely on them correctly function.

Within a dg-driven `defs` project layout, you can apply attribute transformations at any point in the directory structure. This supports uses cases ranging from ensuring that all definitions in a particular folder have an owner set to a particular team to more complex workflows involving applying a group conditionally based on other properties of the definition.

## Example

First, we'll look at a project with assets defined in a subdirectory. You can quickly replicate this example by running the following commands:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/1-scaffold-project.txt" />

There are three assets defined in various subdirectories:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/3-list-defs.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/2-tree.txt" />

Let's say we want to add a `team_a` asset group to all assets in the `team_a` folder. We can add a `component.yaml` file to the `my_project/defs/team_a` directory with the following contents:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/component.yaml"
  language="yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/4-tree.txt" />

Finally, we can run `dg list defs` again to see the new group applied to the assets in the `team_a` subdirectory:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/5-list-defs.txt" />

### Advanced usage

The configuration for the `dagster.components.DefsFolderComponent` can be more complex than the example above. You can apply multiple transforms to the assets in the subdirectory, each of which will be processed in order.

You can also target the configuration to a specific selection of assets using the `target` field. This field uses Dagster's [Selection Syntax](/guides/build/assets/asset-selection-syntax/reference). All selections are evaluated against the assets defined within the subdirectory.
