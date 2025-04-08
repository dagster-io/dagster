---
title: 'Creating a library of components'
sidebar_position: 200
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

`dg` is able to discover declared component types in packages installed in your Python environment. These may come from either your Dagster project or a third-party package. In either case, the mechanism for declaring component types is the same. A package must declare an [entry point](https://packaging.python.org/en/latest/specifications/entry-points/) in the `dagster-dg.library` group in its package metadata. The entry point value is the name of a Python module containing component type definitions. By convention, this usually specifies the top-level module of a package, though any submodule may be specified. The entry point name is  arbitrary and does not affect component type detection, but by convention should be set to the same string as the value (i.e. the module name):

<Tabs>
  <TabItem value="pyproject.toml" label="pyproject.toml">
    ```
    [project.entry-points]
    dagster-dg.library = [
        "my_library = my_library",
    ]
    ```
  </TabItem>
  <TabItem value="setup.py" label="setup.py">
    ```
    setup(
        # ...
        entry_points={
            "dagster_dg.library": [
                "my_library = my_library",
            ],
        },
    )
    ```
  </TabItem>
</Tabs>

Note that scaffolded projects declare `<project_name>.lib` as the entry point by default.
