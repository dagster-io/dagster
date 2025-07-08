---
description: Use template variables to inject dynamic values and functions into your component definitions.
sidebar_position: 300
title: Using template variables
---

Template variables provide a powerful way to make dynamic values and functions available for use when defining components in yaml. Jinja style template injection is applied when loading yaml documents defining component instances, and template variables are the set of things that are available for use in those template expressions.

There are two ways to define template variables:

1. **Template variables module** - Defined as standalone functions in a separate module
2. **Component class static methods** - Defined as `@staticmethod` on a Component class

## Template variables module

The template variables module allows for defining functions in a separate module and are associated with a specific path in the component hierarchy. They can optionally accept a `ComponentLoadContext` parameter, giving you access to the component's loading context.

### Setting up a template variables module

First, create a `template_vars.py` file. We will place it adjacent to the `defs.yaml` since that is the only place using it, though it could be defined elsewhere:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/template_vars.py"
  language="python"
  title="template_vars.py"
/>

Then reference the template variables module in your `defs.yaml` using Jinja template syntax:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/defs.yaml"
  language="yaml"
  title="defs.yaml"
/>

### Module path resolution

The `template_vars_module` field supports both relative and absolute module paths:

- **Relative paths** (starting with `.`) are resolved relative to the current component's module path
- **Absolute paths** specify the full module path

```yaml
# Relative path (recommended for co-located template vars)
template_vars_module: .template_vars

# Absolute path
template_vars_module: my_project.shared.template_vars
```

## Template variable function signatures

Template variable functions can have different signatures depending on whether they need access to the component loading context:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/template_var_context.py"
  language="python"
  title="template_vars.py"
/>

## Component class static methods

Template variables can also be defined directly on your Component class using the `@template_var` decorator on a `@staticmethod`. This approach is useful in cases where you are defining a reusable component and would like all uses of that component to have access to a set of useful template variables

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/component.py"
  language="python"
  title="my_project/components.py"
/>

You can then use these template variables in your component definition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/using-template-variables/component_defs.yaml"
  language="yaml"
  title="defs.yaml"
/>

**Important**: Static template variables must not take any arguments. They are evaluated once when the class is loaded.
