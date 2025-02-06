---
title: Testing configurable resources
sidebar_position: 700
---

You can test the initialization of a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> by constructing it manually. In most cases, the resource can be constructed directly:

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing" endBefore="end_new_resource_testing" />

If the resource requires other resources, you can pass them as constructor arguments:

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing_with_nesting" endBefore="end_new_resource_testing_with_nesting" />

## Testing with resource context

In the case that a resource uses the resource initialization context, you can use the <PyObject section="resources" module="dagster" object="build_init_resource_context"/> utility alongside the `with_init_resource_context` helper on the resource class:

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing_with_context" endBefore="end_new_resource_testing_with_context" />
