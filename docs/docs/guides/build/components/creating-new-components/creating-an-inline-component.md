---
description: Use the dg CLI to create and register an inline component.
sidebar_position: 100
title: Creating an inline component
---

Sometimes you need to define an _ad hoc_ component that you are unlikely to
reuse. In this situation, you can create an **inline component**. An inline
component is a component that is defined in the `defs` directory alongside
its instance definitions, rather than in a directory exposed to the dg registry
(e.g. the `components` directory in a standard `dg` project).

To create an inline component, you can use the `dg scaffold inline-component` command:

```
dg scaffold defs inline-component --typename MyInlineComponent my_inline_component
```

Supposing we are in a project called `my_project`, this will create a new
directory at `my_project/defs/my_inline_component` with two files.

`my_project/defs/my_inline_component/my_inline_component.py` contains a barebones
definition of the `MyInlineComponent` class:

```
import dagster as dg

class SomeComponent(dg.Component, dg.Model, dg.Resolvable):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        return dg.Definitions()
```

`defs/my_inline_component/defs.yaml` defines an instance of the new component:

```yaml
type: my_project.defs.my_inline_component.my_inline_component.MyInlineComponent
attributes: {}
```

Note that there is nothing special about the `type` field-- it is just a
fully-qualified Python object reference, as it is when defining instances of
registered components. The only difference between `MyInlineComponent` and a
registered component is that `MyInlineComponent` won't show up in the `dg`
registry.
