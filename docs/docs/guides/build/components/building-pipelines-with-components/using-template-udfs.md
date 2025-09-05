---
description: Use template variables to inject user-defined functions into component definitions.
sidebar_position: 350
title: Using template UDFs 
---

Template variables can be used to create user-defined functions (UDFs). There is no formal concept of a UDF in dagster. It is just a convention to a describe template variable that is a function.

This is a powerful feature that enables you to inject Python functions into your component YAML definitions. Those functions are evaluated at definition load time, and their output is injected into the YAML document. This can occur anywhere in the document, allowing you to "mix and match" Python and YAML
seamlessly.

## Why UDFs instead of template logic?

Many templating engines offer features like embedded conditionals (`{% if %}`) and loops (`{% for %}`) to handle complex use cases. UDFs are an alternative to this. Instead of using `{% for %}`, you can invoke a Python function that has a `for` loop.

This approach provides several advantages:

- **Clean YAML**: Nested conditionals and for loops often make template documents difficult to parse and reason about.
- **Testing**: You can write unit tests for your configuration logic.
- **Reusability**: You can reuse your UDFs across components.
- **Full IDE support**: Get autocomplete, type checking, and refactoring tools.
- **Maintainability**: Complex business rules are easier to understand and modify in Python.

## Example: Dynamically generating tags

Let's walk through a common scenario where you might start with static YAML configuration, but need to evolve to dynamic generation.

### Starting with static tags

Initially, you might have a simple component with hardcoded compliance tags:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/static_defs.yaml"
  language="yaml"
  title="static_defs.yaml"
/>

This works well at first, but what happens when your compliance requirements become more complex? For example:

- Retention days need to be calculated based on data classification.
- Different rules apply when PII is present.

How do you ensure that these rules are applied generically 

### Evolving to dynamic tag generation

Instead of duplicating this logic across multiple YAML files, you can create a template UDF that generates tags dynamically:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/template_udfs.py"
  language="python"
  title="template_vars.py"
/>

Now you can use this function in your component definition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/dynamic_defs.yaml"
  language="yaml"
  title="dynamic_defs.yaml"
/>

## Using UDFs to incrementally move to Python

The UDF approach allows you to start with simple declarative YAML, then incrementally move to Python without having to alter the schema of the target components.

While one *could* do this by implementing custom schema and then writing the equivalent code within the `build_defs` function of a custom component, the UDF provides a much more more incremental and less disruptive approach:

* You do not have to create a custom component.
* You can use UDFs in definitions where it is need, but still use the simple YAML declarations where it is not, while keeping the component types the same.
* You do not have to teach your users about new schema formats.