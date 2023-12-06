---
title: 'Lesson 3: Overview'
module: 'dagster_essentials'
lesson: '3'
---

## Overview

In Lesson 1, we touched on how an asset-centric approach to writing data pipelines can benefit you and your team. To recap, focusing on assets improves:

- **Context and visibility.** Everyone in your organization can understand the data lineage and how data assets relate to each other
- **Productivity.** By building a DAG that globally understands what data exists and why, asset-centric workflows allow for reusing assets without changing an existing sequence of tasks
- **Observability.** It’s easy to tell exactly why assets are out-of-date, whether it might be late upstream data or errors in code
- **Troubleshooting.** Every run and computation is tied to the goal of producing data, so debugging tools like logs are specific to the assets being produced

Think about the cookie example we started this course with. When the pipeline was **task-centric** - that is, focusing on the steps in the pipeline and not the assets that are produced - it was difficult to tell how a particular asset was produced. When the pipeline was **asset-centric**, however, it was easy to see how assets were created as the steps required to create the asset were **contained within the asset itself.**

In Dagster, the core building block is the **Software-defined Asset (SDA)**. Software-defined assets allow you to write data pipelines by focusing on the assets they produce, making pipelines more debuggable and accessible. SDAs are also commonly referred to as **assets** in the context of Dagster.
