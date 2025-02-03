---
title: Using bare Python objects as resources
sidebar_position: 800
---

When starting to build a set of assets or jobs, you may want to use a bare Python object without configuration as a resource, such as a third-party API client.

Dagster supports passing plain Python objects as resources. This follows a similar pattern to using a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> subclass; however, assets that use these resources must [annotate](https://docs.python.org/3/library/typing.html#typing.Annotated) them with `ResourceParam`. This annotation lets Dagster know that the parameter is a resource and not an upstream input.

{/* TODO replace `ResourceParam` with <PyObject section="resources" module="dagster" object="ResourceParam"/>  */}

```python file=/concepts/resources/pythonic_resources.py startafter=start_raw_github_resource endbefore=end_raw_github_resource dedent=4
from dagster import Definitions, asset, ResourceParam

# `ResourceParam[GitHub]` is treated exactly like `GitHub` for type checking purposes,
# and the runtime type of the github parameter is `GitHub`. The purpose of the
# `ResourceParam` wrapper is to let Dagster know that `github` is a resource and not an
# upstream asset.

@asset
def public_github_repos(github: ResourceParam[GitHub]):
    return github.organization("dagster-io").repositories()

defs = Definitions(
    assets=[public_github_repos],
    resources={"github": GitHub(...)},
)
```
