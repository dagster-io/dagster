---
description: Test initialization of a Dagster ConfigurableResource by constructing it manually.
sidebar_position: 700
title: Testing configurable resources
---

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

You can test the initialization of a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> by constructing it manually. In most cases, the resource can be constructed directly:

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing" endBefore="end_new_resource_testing" dedent="4" title="src/<project_name>/defs/resources.py" />

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_test_my_resource" endBefore="end_test_my_resource" dedent="4" title="tests/test_resource.py" />

If the resource requires other resources, you can pass them as constructor arguments:

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing_with_nesting" endBefore="end_new_resource_testing_with_nesting" dedent="4" title="src/<project_name>/defs/resources.py" />

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_test_my_resource_with_nesting" endBefore="end_test_my_resource_with_nesting" dedent="4" title="tests/test_resource.py" />


## Testing with resource context

In the case that a resource uses the resource initialization context, you can use the <PyObject section="resources" module="dagster" object="build_init_resource_context"/> utility alongside the `with_init_resource_context` helper on the resource class:

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_resource_testing_with_context" endBefore="end_new_resource_testing_with_context" dedent="4" title="src/<project_name>/defs/resources.py" />

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_test_my_context_resource" endBefore="end_test_my_context_resource" dedent="4" title="tests/test_resource.py" />
