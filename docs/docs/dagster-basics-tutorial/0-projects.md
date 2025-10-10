---
title: Projects
description: The Dagster project
sidebar_position: 10
---

Dagster follows standard Python conventions, and most work in Dagster begins by creating a Python package called a [project](/guides/build/projects). This is where you’ll define your pipelines, as well as any dependencies within your project.

To streamline project creation, Dagster provides the [`create-dagster` CLI](/api/clis/create-dagster), which quickly scaffolds a Python package containing a Dagster `Definitions` object. When you scaffold the project, the `Definitions` object will not contain any other Dagster objects.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/definitions.png)

## 1. Scaffold a Dagster project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         uvx create-dagster@latest project dagster-tutorial
         ```

      2. Respond `y` to the prompt to run `uv sync` after scaffolding:

         ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

      3. Change to the `dagster-tutorial` directory:

         ```shell
         cd dagster-tutorial
         ```
      4. Activate the virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

   </TabItem>

   <TabItem value="pip" label="pip">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         create-dagster project dagster-tutorial
         ```
      2. Change to the `dagster-tutorial` directory:

         ```shell
         cd dagster-tutorial
         ```

      3. Create and activate a virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               python -m venv .venv
               ```
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               python -m venv .venv
               ```
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      4. Install your project as an editable package:

         ```shell
         pip install --editable .
         ```

   </TabItem>
</Tabs>

### Dagster project structure

Your new Dagster project should have the following structure:

<Tabs groupId="package-manager">

   <TabItem value="uv" label="uv">
   ```shell
    .
    ├── pyproject.toml
    ├── README.md
    ├── src
    │   └── my_project
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           └── __init__.py
    ├── tests
    │   └── __init__.py
    └── uv.lock
   ```
   </TabItem>
   <TabItem value="pip" label="pip">
   ```shell
    .
    ├── pyproject.toml
    ├── README.md
    ├── src
    │   └── my_project
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           └── __init__.py
    └── tests
        └── __init__.py
   ```
   </TabItem>
</Tabs>

- `pyproject.toml` defines the metadata and Python dependencies for the project.
- The `src` directory will contain code for the project.
- `src/my_project/definitions.py` defines the main Dagster project object.
- The `tests` directory will contain tests for the project.

## 2. Start the Dagster webserver

When you initialize a project with `create-dagster`, the `dagster-dg-cli` library is installed. This provides the `dg` CLI, which includes several commands to help you structure and navigate Dagster projects. For more details, see the [`dg` CLI documentation](/api/clis/dg-cli/dg-cli-configuration).

Use the following command to launch the Dagster UI locally:

<CliInvocationExample contents="dg dev" />

Then, in a browser, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000).

At this point, your project will be empty, but you’ll continue adding to it throughout the tutorial.

![2048 resolution](/images/tutorial/dagster-tutorial/project.png)

:::tip

As you develop with Dagster, it’s often useful to periodically run `dg dev` to view your project.

:::
