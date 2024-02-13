---
title: "Lesson 4: What's a dependency?"
module: 'dagster_essentials'
lesson: '4'
---

# What's a dependency?

A **dependency** is a relationship between assets. Asset dependencies can be:

- **Downstream**, which means an asset is dependent on another asset
- **Upstream**, which means an asset is depended on by another asset

To demonstrate, let’s take a look at a portion of the cookie pipeline.

{% table %}

- {% width="60%; fixed" %}
  In this example, **flour**, **cookie dough**, and **cookies** are our assets. Let’s break down what’s happening here:

  - To make **cookie dough**, **flour** is required. Therefore, **cookie dough** is downstream - or dependent on - **flour.**
  - To make **cookies**, **cookie dough** is required. Therefore, **cookie dough** is upstream - or **cookies** is dependent on - **cookie dough.**

- ![Cookie pipeline, labeled with different types of dependencies](/images/dagster-essentials/lesson-4/cookie-dependencies.png) {% rowspan=2 %}

---

- {% width="60%" %}
  Another way to describe dependencies uses the terms **parent**, **child(ren**), and **ancestor(s).** Let’s take another look at the cookie pipeline to demonstrate how these terms are applied. As these terms are relative to the individual asset, we’ll apply these terms from the perspective of the **cookies** asset.

  - A **child asset** is downstream of its _parent_ asset. In this example, **cookies** is a child of its parent asset, **cookie dough.**
  - An **ancestor** is the parent of a parent asset. In this example, **flour** is the ancestor of **cookies.** This is because **flour** is the parent of **cookie dough**, which is the parent of **cookies.**

- ![Cookie pipeline labels relative to the cookies asset](/images/dagster-essentials/lesson-4/parent-child-ancestor.png) {% rowspan=2 %}

{% /table %}
