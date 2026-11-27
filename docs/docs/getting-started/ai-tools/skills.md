---
title: AI skills for Dagster
description: Learn how to use Dagster's AI skills to build Dagster projects faster, with best practices built in.
sidebar_label: Dagster skills
sidebar_position: 1
---

Dagster maintains an AI skill that gives coding agents better context and patterns for building Dagster projects. With this skill installed, your agent can help you create robust data pipelines according to Dagster best practices.

## About Dagster skills

A **skill** is a structured document that your AI coding agent loads when you invoke it. Skills tell agents what to do and how -- for example, which CLI commands to use, how to structure assets, and which patterns to follow.

Dagster maintains the `dagster-expert` skill in the [dagster-io/skills](https://github.com/dagster-io/skills) repository. It provides expert guidance for building production-quality Dagster projects, covering [`dg`](/api/clis/cli) CLI usage, asset patterns, automation strategies, and implementation workflows.

## Installing Dagster skills

We recommend installing Dagster skills with the `dagster` plugin. See the [Dagster plugin](/getting-started/ai-tools/plugin) page for installation instructions.

Skills can also be installed using the [`npx skills`](https://www.skills.sh/) command line:

```text
npx skills add dagster-io/skills#release-stable
```

This will install the `dagster-expert` skill into every agent `npx` detects.

:::warning

The `dagster-expert` skill was previously published as part of a plugin called `dagster-expert`. As of September 14, 2026, the `dagster-expert` plugin is deprecated and the `dagster-expert` skill is published as part of the `dagster` plugin. The `dagster-expert` skill itself is unchanged and is still invoked with `/dagster-expert`.

The `dagster-expert` plugin remains installable to prevent sudden breakages, but has been replaced with a stub skill that carries no guidance and points to instructions to migrate to the `dagster` plugin. To migrate, uninstall the `dagster-expert` plugin and follow the installation instructions for the `dagster` plugin.

:::

## Invoking Dagster skills

Many agents will automatically load relevant skills based on the session. To directly invoke the `dagster-expert` skill, you can use the namespaced format:

```text
/dagster-expert create a new Dagster project called my-pipeline
```

## Next steps

- Follow the [Quickstart](/getting-started/quickstart) to scaffold your first Dagster project
- Learn more in the [AI-Driven Data Engineering](https://courses.dagster.io/) course on Dagster University
