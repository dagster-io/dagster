---
description: Dagster supports passing bare Python objects in asset definitions as resources.
sidebar_position: 800
title: Using bare Python objects as resources
---

import ScaffoldResource from '@site/docs/partials/\_ScaffoldResource.md';

<ScaffoldResource />

When starting to build a set of assets or jobs, you may want to use a bare Python object without configuration as a resource, such as a third-party API client.

Dagster supports passing bare Python objects as resources. This follows a similar pattern to using a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> subclass; however, assets that use these resources must [annotate](https://docs.python.org/3/library/typing.html#typing.Annotated) them with `ResourceParam`. This annotation lets Dagster know that the parameter is a resource and not an upstream input.

{/* TODO replace `ResourceParam` with <PyObject section="resources" module="dagster" object="ResourceParam"/>  */}

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_raw_github_resource" endBefore="end_raw_github_resource" dedent="4" title="src/<project_name>/defs/assets.py" />

<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_raw_github_resource_defs" endBefore="end_raw_github_resource_defs" dedent="4" title="src/<project_name>/defs/resources.py" />