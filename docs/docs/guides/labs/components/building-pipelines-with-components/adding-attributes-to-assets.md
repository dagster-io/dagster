---
title: 'Adding attributes to assets in a subdirectory'
sidebar_position: 550
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

Attaching and modifying meta information on definitions such as assets is important in Dagster projects. You want to have groups, teams, owners, kinds, tags, and metadata set correctly to organize definitions and ensure that other tools and processes that rely on them correctly function.

Within a dg-driven `defs` project layout, you can apply metadata transformations at any point in the folder structure. This can span uses cases from ensuring that all definitions in a particular folder have a tag associating them with the same team, to more complex workflows of applying a group conditionally based on other properties of the definition.

### Example

First, we can look at an existing project, where we have assets defined in a subdirectory:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/2-list-defs.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/1-tree.txt" />

Now, we can add a `component.yaml` file to the `my_project/defs/team_a` directory with the following contents:

<CodeExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/component.yaml" language="yaml" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/3-tree.txt" />

This configuration will set the group of all assets within the directory to `team_a`.

Finally, we can run `dg list defs` again to see the new group applied to the assets in the `team_a` subdirectory:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-attributes-to-assets/4-list-defs.txt" />

### Advanced Usage

The configuration for the `dagster.components.DefsFolderComponent` can be more complex than the example above. You can apply multiple transforms to the assets in the subdirectory, each of which will be processed in order.

You can also target the configuration to a specific selection of assets using the `target` field. This field uses Dagster's [Selection Syntax](/guides/build/assets/asset-selection-syntax/reference). All selections are evaluated against the assets defined within the subdirectory.