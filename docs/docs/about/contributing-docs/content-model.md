---
title: Dagster documentation content model
sidebar_label: Content model
description: A guide to Dagster documentation structure and types.
---

This page describes the structure and types of documentation we write at Dagster.

A content model helps writers structure content so it is usable by readers. The basic types of [conceptual](#conceptual-content), [procedural](#procedural-content), and [reference](#reference-content) content can be combined in a single page as needed, or used to format standalone pages, which can themselves be combined into longer guides or tutorials.

This content model can also help you write documentation that make sense to readers accessing or navigating the docs in a [non-linear way](https://idratherbewriting.com/trends/trends-to-follow-or-forget-every-page-is-page-one.html).

## Conceptual content

Conceptual content answers the question "What is this and why is it important?" Many section index pages in our docs contain conceptual content. These pages and sections are often titled "[X]", or "About [X]", where X is a concept or feature, for instance, "Assets", "Components", "Partitions and backfills".

### Examples

- [Assets section index page](https://docs.dagster.io/guides/build/assets/)
- [Top section of external assets page](https://docs.dagster.io/guides/build/assets/external-assets) (before "Defining external assets")
- [Top section of Declarative Automation section index page](https://docs.dagster.io/guides/automate/declarative-automation/) (before "Using Declarative Automation").

## Procedural content

Procedural content answers the question "How do I…?" Conceptual content docs are often titled "Doing [X]" or "Do [X]", e.g. "Creating assets" or "Build pipelines with Databricks".

### Examples

- [Build pipelines with Databricks](https://docs.dagster.io/guides/build/external-pipelines/databricks-pipeline)
- [Creating alert policies](https://docs.dagster.io/guides/observe/alerts/creating-alerts)
- [Creating Dagster projects](https://docs.dagster.io/guides/build/projects/creating-projects)

## Reference content

Reference content answers the question "What are the pieces?". Reference content docs are often titled with nouns or noun phrases, e.g. "Asset types" or "Dagster project file reference".

### Examples

- [Dagster project structure overview](https://docs.dagster.io/guides/build/projects/project-structure/project-overview)
- [Asset selection syntax reference](https://docs.dagster.io/guides/build/assets/asset-selection-syntax/reference)
- [Alert policy types](https://docs.dagster.io/guides/observe/alerts/alert-policy-types)

## Bringing it all together

Here are some examples of docs that use a combination of conceptual, procedural, and reference content to document a single feature or product area:

### Kind tags page

The [kind tags page](https://docs.dagster.io/guides/build/assets/metadata-and-tags/kind-tags) contains all three content types:

- A conceptual section at the top
- A procedural section ("Adding kinds to an asset")
- Another procedural section ("Adding compute kinds to assets")
- A reference section ("Supported icons")
- A very short procedural section at the bottom ("Requesting additional icons")

### Declarative Automation docs

- The [index page](https://docs.dagster.io/guides/automate/declarative-automation) of the Declarative Automation docs section contains a conceptual section that introduces the reader to Declarative Automation, followed by a short reference section ([Recommended automation conditions](https://docs.dagster.io/guides/automate/declarative-automation#recommended-automation-conditions)) that describes the `AutomationCondition` object and briefly describes basic built-in conditions that should suffice for most users just getting started with Declarative Automation.
- The [Customizing automation conditions](https://docs.dagster.io/guides/automate/declarative-automation/customizing-automation-conditions) subsection contains several pages of procedural documentation about customizing the built-in automation conditions `on_cron`, `on_missing`, and `eager`, as well as a page on describing automation conditions with labels.
- [Automating asset checks](https://docs.dagster.io/guides/automate/declarative-automation/automating-asset-checks) is a procedural page
- [Automation condition sensors](https://docs.dagster.io/guides/automate/declarative-automation/automation-condition-sensors) contains a conceptual introduction to automation condition sensors, followed by procedural content on adding additional sensors, defaulting to a running state, and adding run tags.
- [Automation condition reference](https://docs.dagster.io/guides/automate/declarative-automation/automation-condition-reference) is a reference doc that contains tables of automation condition operands, operators, composite conditions, evaluations, statuses and events, and information on run grouping. Users can consult this reference when building up custom automation conditions.
