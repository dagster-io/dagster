---
title: "Linking to asset definition code with code references"
---

:::note Experimental feature

This feature is considered **experimental** and is under active development. This guide will be updated as we roll out new features.

:::

Attaching code reference metadata to your Dagster asset definitions allows you to easily view those assets' source code from the Dagster UI:

- **In local development**, navigate directly to the code backing an asset in your editor
- **In your production environment**, link to source code in your source control repository to see the full change history for an asset

In this guide, we'll show you how to automatically and manually attach code references to your Dagster assets.

## Prerequisites

To complete the steps in this guide, you'll need:

- A set of Dagster asset definitions that you want to link to code
- Dagster version `1.7.6` or newer

## Automatically attaching local file code references to asset definitions

### Assets defined in Python

To automatically attach code references to Python assets' function definitions, you can use the <PyObject section="metadata" module="dagster" object="with_source_code_references"/> utility. Any asset definitions passed to the utility will have their source file attached as metadata.

For example, given the following Python file `with_source_code_references.py`:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/code_references/with_source_code_references.py
from dagster import Definitions, asset, with_source_code_references


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(assets=with_source_code_references([my_asset, another_asset]))
```

A link to the asset's source in `with_source_code_references.py` will then be visible in the **Asset Catalog** view in the Dagster UI:

![Asset catalog view showing link to with_source_code_references.py](/images/guides/build/assets/metadata-tags/code-references/with_source_code_references.png)

### dbt assets

Dagster's dbt integration can automatically attach references to the SQL files backing your dbt assets. For more information, see the [dagster-dbt integration reference](/integrations/libraries/dbt/reference#attaching-code-reference-metadata).

## Manually attaching local file code references to asset definitions

In some cases, you may want to manually attach code references to your asset definitions. Some assets may have a more complex source structure, such as an asset whose definition is spread across multiple Python source files or an asset which is partially defined with a `.sql` model file.

To manually attach code references to an asset definition, use <PyObject section="metadata" module="dagster" object="CodeReferencesMetadataValue"/>. You can then choose to augment these manual references with <PyObject section="metadata" module="dagster" object="with_source_code_references"/>:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/code_references/manual_references.py
import os

from dagster import (
    CodeReferencesMetadataValue,
    Definitions,
    LocalFileCodeReference,
    asset,
    with_source_code_references,
)


@asset(
    metadata={
        "dagster/code_references": CodeReferencesMetadataValue(
            code_references=[
                LocalFileCodeReference(
                    file_path=os.path.join(os.path.dirname(__file__), "source.yaml"),
                    # Label and line number are optional
                    line_number=1,
                    label="Model YAML",
                )
            ]
        )
    }
)
def my_asset_modeled_in_yaml(): ...


defs = Definitions(assets=with_source_code_references([my_asset_modeled_in_yaml]))
```

Each of the code references to `manual_references.py` will be visible in the **Asset details** page in the Dagster UI:

![Asset details view showing link to multiple files](/images/guides/build/assets/metadata-tags/code-references/manual_references.png)

## Converting code references to link to a remote git repository

In a local context, it is useful to specify local code references in order to navigate directly to the source code of an asset. However, in a production environment, you may want to link to the source control repository where the code is stored.

### In Dagster Plus

If using Dagster Plus, you can use the `link_code_references_to_git_if_cloud` utility to conditionally convert local file code references to source control links. This utility will automatically detect if your code is running in a Dagster Cloud environment and convert local file code references to source control links, pointing at the commit hash of the code running in the current deployment.

<!-- Dagster cloud packages not built into docs image yet, hence why this is included inline -->

```python
import os
from pathlib import Path

from dagster_cloud.metadata.source_code import link_code_references_to_git_if_cloud

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    asset,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(
    assets=link_code_references_to_git_if_cloud(
        assets_defs=with_source_code_references([my_asset, another_asset]),
        # Inferred from searching for .git directory in parent directories
        # of the module containing this code - may also be set explicitly
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
)
```

### In any Dagster environment

The <PyObject section="metadata" module="dagster" object="link_code_references_to_git"/> utility allows you to convert local file code references to source control links. You'll need to provide the base URL of your git repository, the branch or commit hash, and a <PyObject section="metadata" module="dagster" object="FilePathMapping"/> which tells Dagster how to convert local file paths to paths in the repository. The simplest way to do so is with an <PyObject section="metadata" module="dagster" object="AnchorBasedFilePathMapping"/>, which uses a local file path and the corresponding path in the repository to infer the mapping for other files.

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/code_references/link_to_source_control.py
from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    asset,
    link_code_references_to_git,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


defs = Definitions(
    assets=link_code_references_to_git(
        assets_defs=with_source_code_references([my_asset, another_asset]),
        git_url="https://github.com/dagster-io/dagster",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
)
```

You may choose to conditionally apply this transformation based on the environment in which your Dagster code is running. For example, you could use an environment variable to determine whether to link to local files or to a source control repository:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/code_references/link_to_source_control_conditional.py
import os
from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    Definitions,
    asset,
    link_code_references_to_git,
    with_source_code_references,
)


@asset
def my_asset(): ...


@asset
def another_asset(): ...


assets = with_source_code_references([my_asset, another_asset])

defs = Definitions(
    assets=link_code_references_to_git(
        assets_defs=assets,
        git_url="https://github.com/dagster-io/dagster",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository="src/repo.py",
        ),
    )
    if bool(os.getenv("IS_PRODUCTION"))
    else assets
)
```
