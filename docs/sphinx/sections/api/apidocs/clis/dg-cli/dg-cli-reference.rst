dg CLI
======

.. currentmodule:: dagster_dg_cli

.. click:: dagster_dg_cli.cli.check:check_group
    :prog: dg check
    :nested: full

.. click:: dagster_dg_cli.cli.dev:dev_command
    :prog: dg dev
    :nested: full

.. click:: dagster_dg_cli.cli.launch:launch_command
    :prog: dg launch
    :nested: full

.. click:: dagster_dg_cli.cli.list:list_group
    :prog: dg list
    :nested: full

.. click:: dagster_dg_cli.cli.plus:plus_group
    :prog: dg plus
    :nested: full

.. click:: dagster_dg_cli.cli.scaffold:scaffold_group
    :prog: dg scaffold
    :nested:


dg scaffold example
^^^^^^^^^^^^^^^^^^^

**Note:** Before scaffolding definitions with ``dg``, you must `create a project <https://docs.dagster.io/guides/build/projects/creating-a-new-project>`_ with the `create-dagster CLI <https://docs.dagster.io/api/clis/create-dagster>`_ and activate its virtual environment.

You can use the ``dg scaffold defs`` command to scaffold a new asset underneath the ``defs`` folder. In this example, we scaffold an asset named ``my_asset.py`` and write it to the ``defs/assets`` directory:

.. code-block:: bash

    dg scaffold defs dagster.asset assets/my_asset.py

    Creating a component at /.../my-project/src/my_project/defs/assets/my_asset.py.


Once the asset has been scaffolded, we can see that a new file has been added to ``defs/assets``, and view its contents:

.. code-block:: bash

    tree

    .
    ├── pyproject.toml
    ├── src
    │ └── my_project
    │     ├── __init__.py
    │     └── defs
    │         ├── __init__.py
    │         └── assets
    │             └── my_asset.py
    ├── tests
    │ └── __init__.py
    └── uv.lock


.. code-block:: python

    cat src/my_project/defs/assets/my_asset.py

    import dagster as dg


    @dg.asset
    def my_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...


**Note:** You can run ``dg scaffold defs`` from within any directory in your project and the resulting files will always be created in the ``<project-name>/src/<project_name>/defs/`` folder.

In the above example, the scaffolded asset contains a basic commented-out definition. You can replace this definition with working code:

.. code-block:: python

    import dagster as dg


    @dg.asset(group_name="my_group")
    def my_asset(context: dg.AssetExecutionContext) -> None:
        """Asset that greets you."""
        context.log.info("hi!")


To confirm that the new asset now appears in the list of definitions, run `dg list defs`:

.. code-block:: bash

    dg list defs

    ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Section ┃ Definitions                                                     ┃
    ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ Assets  │ ┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓ │
    │         │ ┃ Key      ┃ Group    ┃ Deps ┃ Kinds ┃ Description            ┃ │
    │         │ ┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩ │
    │         │ │ my_asset │ my_group │      │       │ Asset that greets you. │ │
    │         │ └──────────┴──────────┴──────┴───────┴────────────────────────┘ │
    └─────────┴─────────────────────────────────────────────────────────────────┘
