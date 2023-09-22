---
title: 'Lesson 6: Lesson recap'
module: 'dagster_essentials'
lesson: '6'
---

# Lesson recap

Dagster comes with many resources and integrations out of the box. However, an integration library is not required to use your tools within Dagster.

You can pass any object or connection into your code location’s `Definitions` and add it as a resource. The only requirement is that you will need to add `ResourceParam[<ClassName>]` to your asset argument’s type hints for your asset function to understand that you’re referencing a resource.

Check out the [Dagster Docs](https://docs.dagster.io/integrations) for more info about all of Dagster’s integrations.

{% callout %}

> ‼️ Make sure you update your code to match the practice problem answer before continuing!

{% /callout %}
