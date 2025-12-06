---
description: Learn how to organize a Dagster project by technology or concept.
sidebar_position: 300
title: Organizing your Dagster project
---

import TreeTip from '@site/docs/partials/\_TreeTip.md';

There are many ways to structure your Dagster project, and it can be difficult to know where to start. In this guide, we will walk you through our recommendations for organizing your Dagster project.

## Initial project structure

When you first [create a project using the `create-dagster` CLI](/guides/build/projects/creating-projects), it looks like the following:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">

  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/uv-tree-project.txt" />

  </TabItem>
  <TabItem value="pip" label="pip">

  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/pip-tree-project.txt" />

  </TabItem>
</Tabs>

<TreeTip />

This is a reasonable structure when you are first getting started. However, as you begin to introduce more assets, jobs, resources, sensors, and utility code, you may find that your Python files are growing too large to manage.

## Reorganizing your project

Deciding how to organize your project is often influenced by how you and your team members operate. This guide will outline two possible project structures: **organized by technology**, and **organized by concept**.

<Tabs>
  <TabItem value="tech" label="Organized by technology">

  Data engineers often have a strong understanding of the underlying technologies that are used in their data pipelines. Because of that, it's often helpful to organize your project by technology. This enables engineers to easily navigate the codebase and locate files pertaining to the specific technology.

  Within the technology modules, submodules can be created to further organize your code.

  <Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
  
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/uv-project-by-tech.txt" />

  </TabItem>
  <TabItem value="pip" label="pip">
  
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/pip-project-by-tech.txt" />

  </TabItem>
  </Tabs>

  </TabItem>
  <TabItem value="concept" label="Organized by concept">

You can also organize your project by data processing concept -- for example, data transformation, ingestion, or processing. This provides additional context to engineers who may not be as familiar with the underlying technologies.

  <Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">

  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/uv-project-by-concept.txt" />

  </TabItem>
  <TabItem value="pip" label="pip">
  
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/projects/pip-project-by-concept.txt" />

  </TabItem>
  </Tabs>
</TabItem>
</Tabs>

## External projects

As your data platform evolves, you can integrate other data tools, such as dbt, Sling, or Jupyter notebooks.

We recommended storing these projects outside your Dagster project, as demonstrated in the `dbt_project` example below.

```shell
.
├── dbt_project/
│   ├── config/
│   │   └── profiles.yml
│   ├── dbt_project.yml
│   ├── macros/
│   │   ├── aggregate_actions.sql
│   │   └── generate_schema_name.sql
│   ├── models/
│   │   ├── activity_analytics/
│   │   │   ├── activity_daily_stats.sql
│   │   │   ├── comment_daily_stats.sql
│   │   │   └── story_daily_stats.sql
│   │   ├── schema.yml
│   │   └── sources.yml
│   └── tests/
│       └── assert_true.sql
└── example-dagster-project/
```

:::info Using a workspace to manage multiple projects

This guide outlines how to structure a single Dagster project. Most people will only need one project. However, Dagster also allows you to create a workspace with multiple projects.

A helpful pattern uses a workspace with multiple projects to separate conflicting dependencies, where each project has its own package requirements and deployment specs. For more information, see [Creating workspaces to manage multiple projects](/guides/build/projects/workspaces/creating-workspaces).

:::