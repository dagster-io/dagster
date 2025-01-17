---
title: Defining assets that depend on other assets
sidebar_position: 200
---

Asset definitions can depend on other asset definitions. The dependent asset is called the **downstream asset**, and the asset it depends on is the **upstream asset**.

## Defining basic dependencies

You can define a dependency between two assets by passing the upstream asset to the `deps` parameter in the downstream asset's `@asset` decorator.

In this example, the asset `sugary_cereals` creates a new table (`sugary_cereals`) by selecting records from the `cereals` table. Then the asset `shopping_list` creates a new table (`shopping_list`) by selecting records from `sugary_cereals`:

<CodeExample filePath="" language="python" lineStart="" lineEnd=""/>

## Defining asset dependencies across code locations

Assets can depend on assets in different [code locations](/guides/deploy/code-locations/). In the following example, the `code_location_1_asset` asset produces a JSON string from a file in `code_location_1`:

<CodeExample filePath="" language="python" lineStart="" lineEnd=""/>

In `code_location_2`, we can reference `code_location_1_asset` it via its asset key:

<CodeExample filePath="" language="python" lineStart="" lineEnd=""/>

