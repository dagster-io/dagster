---
title: "Extra credit: What's metadata?"
module: 'dagster_essentials'
lesson: 'extra-credit'
---

# What's metadata?

Two of the core benefits of Dagster are collaboration between engineers and cross-functionally sharing assets. Even if you’re a team of one, the documentation of your pipelines will help with debugging and providing context for code a few months after you write it.

In this lesson, we’ll cover two types of metadata: definition and **materialization.** We’ll go back to our cookie example to explain each type.

---

## Definition metadata

{% table %}

- {% width="60%" %}
  _Definition_ metadata is, by definition, information that is fixed or doesn’t frequently change.

  In the context of cookies, a piece of definition metadata might be a serving suggestion like the following.

- ![This serving suggestion, a piece of definition metadata, will help you enjoy cookies in the best way](/images/dagster-essentials/extra-credit/definition-cookies.png) {% rowspan=2 %}

{% /table %}

---

## Materialization metadata

{% table %}

- {% width="60%" %}
  _Materialization_ metadata is dynamic, meaning the information changes after an action occurs.

  In the context of cookies, materialization metadata could be the date a batch of cookies was baked, who baked them, and how many cookies are in the batch.

- ![This information, collected after cookies were baked, is an example of materialization metadata](/images/dagster-essentials/extra-credit/materialization-cookies.png) {% rowspan=2 %}

{% /table %}

---

## How does this fit in with Dagster?

Using definition metadata to describe assets can make it easy to provide context for your team and your future self. This metadata could be descriptions of the assets, the types of assets, and how they fit into the larger picture of your organization’s data.

Then, at runtime, you can use metadata to surface information about the materialization such as how many records were processed or when the materialization occurred.

We'll start by discussing definition metadata, where we'll walk you through adding descriptions to assets and adding them to groups.
