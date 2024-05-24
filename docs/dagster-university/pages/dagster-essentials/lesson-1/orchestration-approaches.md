---
title: 'Lesson 1: Orchestration approaches'
module: 'dagster_essentials'
lesson: '1'
---

# Orchestration approaches

Data engineers see orchestration as key to solidifying a data pipeline for business and real-world use. In this section, we’ll go through two different approaches to workflow orchestration and the pros and cons of each.

But first, what’s a workflow?

{% callout %}

> A workflow is a system for managing repetitive processes and tasks which occur in a particular order. They are the mechanism by which people and enterprises accomplish their work \[…].\_ - [IBM](https://www.ibm.com/topics/workflow) >

{% /callout %}

A workflow can be visualized using a **directed acyclic graph,** or **DAG**, which depicts the steps required to complete the workflow. For example, sending a CSV of a report by email every Friday might have a DAG that looks like this:

![An email task as a DAG](/images/dagster-essentials/demo/lesson-1-email-as-dag.png)

As we mentioned, there are different approaches to orchestrating workflows, and we’ll focus on two: **task-centric** and **asset-centric**. We’ll use an example of each approach using a pipeline to bake a popular treat: **cookies.**

---

## Task-centric workflow orchestration

Task-centric orchestration is a methodology that focuses on managing and coordinating the execution of tasks. It focuses on the **hows** and less on the **whats**.

For example, data engineers often perform tasks such as pulling data from an API, cleaning it, and loading it to a destination to perform analytics on it, a process known as ETL.

### Example of a task-centric workflow

It’s time to bring in the cookies! If you were to set up a task-centric workflow to bake cookies, it would look like this:

1. Gather ingredients
2. Combine ingredients
3. Add chocolate chips
4. Bake in the oven
5. Enjoy freshly baked **chocolate chip cookies**

![Baking chocolate cookies as a task-centric workflow](/images/dagster-essentials/demo/lesson-1-cookie-etl.png)

This workflow is sequential and focused on the **tasks** required to create the cookies. Notice how at the end, after all steps have been completed, there’s only one obvious output: the freshly baked cookies.

We’ve added the other outputs that are created along the way to the DAG - **cookie dough** and **chocolate chip cookie dough** - but as this approach focuses on tasks, it’s not immediately obvious where or how outputs are created.

---

## Asset-centric workflow orchestration

Workflows that make things (whether they might be chocolate chip cookies or data) have different needs than task-centric workflows when building, troubleshooting, or scaling them. _Assets_ are what we call the outputs made by workflows. Asset-centric workflows make it easy to, at a glance, focus on the **whats** and less on the **hows.**

### Example of asset-centric workflow

Let’s re-work our cookie workflow to use an **asset-centric** approach. We’ll still wind up with freshly baked cookies, but this time, the DAG will look a bit different. Specifically, our cookie graph will primarily contain **nouns** and fewer **verbs**, or instructions.

With an asset-centric approach, upstream assets are used as inputs to create their downstream dependencies. For example:

- To create the **cookie dough,** combine the **wet ingredients** and **dry ingredients**
- To create the **chocolate chip cookie dough**, mix the **chocolate chips** into the **cookie dough**
- Lastly, bake the **chocolate chip cookie dough** and wind up with **freshly baked chocolate chip cookies!**

![Baking chocolate cookies as an asset-centric workflow](/images/dagster-essentials/demo/lesson-1-cookie-assets-one-cookie.png)

### Expanding by adding more assets

An asset-centric approach also makes adding additional assets straightforward. For example, let’s say you also wanted to bake some **peanut cookies.** To do this, you could:

- Add **peanuts** to the **raw ingredients**
- To create the **peanut cookie dough**, mix the **peanuts** into the **cookie dough**
- Lastly, bake the **peanut cookie dough** and wind up with **freshly baked peanut cookies!**

_Voila_! By adding only one additional asset - **peanuts** - we were able to use some of our existing assets to create something brand new - **peanut cookies** - with minimal alterations. Check out the new additions to the DAG (highlighted in light purple) to the right.

![Adding peanut cookies to the asset-centric cookie workflow](/images/dagster-essentials/demo/lesson-1-cookie-assets-two-cookies.png)

So, how might this be beneficial to a real data pipeline? **Reusability.**

In a task-centric workflow, assets are closely coupled with the tasks that create them. This can make re-using assets difficult, as they are more of a by-product than the focus.

An asset could be added to an existing workflow even if it’s not fully relevant to it, resulting in tech debt. Or, it could be added to a new workflow, which would require running an existing workflow, thereby reducing observability, understanding, and data lineage.
