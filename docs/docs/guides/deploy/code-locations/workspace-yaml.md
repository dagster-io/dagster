---
title: 'Workspace file (workspace.yaml) reference'
sidebar_position: 200
---

:::info

This reference is only applicable to Dagster OSS. For Dagster+, see [the Dagster+ code locations documentation](/dagster-plus/deployment/code-locations).

:::

A workspace file is used to configure code locations in Dagster. It tells Dagster where to find your code and how to load it. By default, this is a YAML document named workspace.yaml. For example:

```yaml
# workspace.yaml

load_from:
  - python_file: my_file.py
```

Each entry in a workspace file is considered a code location. A code location should contain a single <PyObject section="definitions" module="dagster" object="Definitions" /> object.

Each code location is loaded in its own process that Dagster tools use an RPC protocol to communicate with. This process separation allows multiple code locations in different environments to be loaded independently, and ensures that errors in user code can't impact Dagster system code.

:::info Migrating from `@repository` to `Definitions`

To accommodate incrementally migrating from `@repository` to `Definitions`, code locations in a single workspace file can mix and match between definition approaches. For example, `code-location-1` could load a single `Definitions` object from a file or module, and `code-location-2` could load multiple repositories.

:::

## Location of workspace.yaml

Dagster command-line tools (like `dagster dev`, `dagster-webserver`, or `dagster-daemon run`) look for workspace files in the current directory when invoked. This allows you to launch from that directory without the need for command line arguments

To load the workspace.yaml file from a different folder, use the -w argument:

```bash
dagster dev -w path/to/workspace.yaml
```

## File structure

The `workspace.yaml` file uses the following structure:

```yaml
load_from:
  - <loading_method>: <configuration_options>
```

Where `<loading_method>` can be one of:

- `python_file`
- `python_module`
- `grpc_server`

## Loading code locations

We recommend loading from a Python module for most cases.

:::note

Each code location is loaded in its own process.

:::

### Python module

To load a code location from a local or installed Python module, use the `python_module` key in workspace.yaml.

**Options:**

- `module_name`: Name of the Python module to load.
- Other options are the same as `python_file`.

**Example:**

```yaml
load_from:
  - python_module:
      module_name: hello_world_module.definitions
```

### Python file

To load a code location from a Python file, use the `python_file` key in workspace.yaml. The value of `python_file` should specify a path relative to `workspace.yaml` leading to a file that contains a code location definition.

**Options:**

- `relative_path`: Path to the Python file, relative to the `workspace.yaml` location.
- `attribute` (optional): Name of a specific repository or function returning a `RepositoryDefinition`.
- `working_directory` (optional): Custom working directory for relative imports.
- `executable_path` (optional): Path to a specific Python executable.
- `location_name` (optional): Custom name for the code location.

**Example:**

```yaml
load_from:
  - python_file:
      relative_path: hello_world_repository.py
      attribute: hello_world_repository
      working_directory: my_working_directory/
      executable_path: venvs/path/to/python
      location_name: my_location
```

:::info Using @repository

If using `@repository` to define code locations, you can identify a single repository within the module using the `attribute` key. The value of this key must be the name of a repository or the name of a function that returns a <PyObject section="repositories" module="dagster" object="RepositoryDefinition" />. For example:

```yaml
# workspace.yaml

load_from:
  - python_file:
      relative_path: hello_world_repository.py
      attribute: hello_world_repository
```

:::

### gRPC server

Configures a gRPC server as a code location.

**Options:**

- `host`: The host address of the gRPC server.
- `port`: The port number of the gRPC server.
- `location_name`: Custom name for the code location.

**Example:**

```yaml
load_from:
  - grpc_server:
      host: localhost
      port: 4266
      location_name: 'my_grpc_server'
```

## Multiple code locations

You can define multiple code locations in a single `workspace.yaml` file:

```yaml
load_from:
  - python_file:
      relative_path: path/to/dataengineering_spark_team.py
      location_name: dataengineering_spark_team_py_38_virtual_env
      executable_path: venvs/path/to/dataengineering_spark_team/bin/python
  - python_file:
      relative_path: path/to/team_code_location.py
      location_name: ml_team_py_36_virtual_env
      executable_path: venvs/path/to/ml_tensorflow/bin/python
```

## Loading workspace files

By default, Dagster command-line tools (like `dagster dev`, `dagster-webserver`, or `dagster-daemon run`) look for workspace files (by default, `workspace.yaml`) in the current directory when invoked. This allows you to launch from that directory without the need for command line arguments:

```shell
dagster dev
```

To load the `workspace.yaml` file from a different folder, use the `-w` argument:

```shell
dagster dev -w path/to/workspace.yaml
```

When `dagster dev` is run, Dagster will load all the code locations defined by the workspace file. For more information and examples, see the [CLI reference](/api/python-api/cli#dagster-dev).

If a code location can't be loaded - for example, due to a syntax error or other unrecoverable error - a warning message will display in the Dagster UI. You'll be directed to a status page with a descriptive error and stack trace for any locations Dagster was unable to load.

:::info

If a code location is renamed or its configuration in a workspace file is modified, you must stop and restart any running schedules or sensors in that code location. You can do this in the UI by navigating to the [**Deployment overview** page](/guides/operate/webserver#deployment), clicking a code location, and using the **Schedules** and **Sensors** tabs.

:::

## Running your own gRPC server

By default, Dagster tools automatically create a process on your local machine for each of your code locations. However, it's also possible to run your own gRPC server that's responsible for serving information about your code locations. This can be useful in more complex system architectures that deploy user code separately from the Dagster webserver.

- [Initializing the server](#initializing-the-server)
- [Specifying a Docker image](#specifying-a-docker-image)

### Initializing the server

To initialize the Dagster gRPC server, run the `dagster api grpc` command and include:

- A target file or module. Similar to a workspace file, the target can either be a Python file or module.
- Host address
- Port or socket

The following tabs demonstrate some common ways to initialize a gRPC server:

<Tabs>
<TabItem value="Using a Python file">

Running on a port, using a Python file:

```shell
dagster api grpc --python-file /path/to/file.py --host 0.0.0.0 --port 4266
```

Running on a socket, using a Python file:

```shell
dagster api grpc --python-file /path/to/file.py --host 0.0.0.0 --socket /path/to/socket
```

</TabItem>
<TabItem value="Using a Python module">

Using a Python module:

```shell
dagster api grpc --module-name my_module_name.definitions --host 0.0.0.0 --port 4266
```

</TabItem>
<TabItem value="Using a specific repository">

:::note

This only applies to code locations defined with <PyObject section="repositories" module="dagster" object="repository" decorator />.

:::

Specifying an attribute within the target to load a specific repository. When run, the server will automatically find and load the specified repositories:

```shell
dagster api grpc --python-file /path/to/file.py --attribute my_repository --host 0.0.0.0 --port 4266
```

</TabItem>
<TabItem value="Local imports">

Specify a working directory to use as the base folder for local imports:

```shell
dagster api grpc --python-file /path/to/file.py --working-directory /var/my_working_dir --host 0.0.0.0 --port 4266
```

</TabItem>
</Tabs>

Refer to the [API docs](/api/python-api/cli#dagster-api-grpc) for the full list of options that can be set when running a new gRPC server.

Then, in your workspace file, configure a new gRPC server code location to load:

```yaml file=/concepts/repositories_workspaces/workspace_grpc.yaml
# workspace.yaml

load_from:
  - grpc_server:
      host: localhost
      port: 4266
      location_name: 'my_grpc_server'
```

### Specifying a Docker image

When running your own gRPC server within a container, you can tell the webserver that any runs launched from a code location should be launched in a container with that same image.

To do this, set the `DAGSTER_CURRENT_IMAGE` environment variable to the name of the image before starting the server. After setting this environment variable for your server, the image should be listed alongside the code location on the **Status** page in the UI.

This image will only be used by [run launchers](/guides/deploy/execution/run-launchers) and [executors](/guides/operate/run-executors) that expect to use Docker images (like the <PyObject section="libraries" module="dagster_docker" object="DockerRunLauncher" />, <PyObject section="libraries" module="dagster_k8s" object="K8sRunLauncher" />, <PyObject section="libraries" module="dagster_docker" object="docker_executor" />, or <PyObject section="libraries" module="dagster_k8s" object="k8s_job_executor" />).

If you're using the built-in [Helm chart](/guides/deploy/deployment-options/kubernetes/deploying-to-kubernetes), this environment variable is automatically set on each of your gRPC servers.

## Examples

<Tabs>
<TabItem value="Loading relative imports">

### Loading relative imports

By default, code is loaded with `dagster-webserver`'s working directory as the base path to resolve any local imports in your code. Using the `working_directory` key, you can specify a custom working directory for relative imports. For example:

<CodeExample path="docs_snippets/docs_snippets/concepts/repositories_workspaces/workspace_working_directory.yaml" />

</TabItem>
<TabItem value="Loading multiple Python environments">

### Loading multiple Python environments

By default, the webserver and other Dagster tools assume that code locations should be loaded using the same Python environment used to load Dagster. However, it's often useful for code locations to use independent environments. For example, a data engineering team running Spark can have dramatically different dependencies than an ML team running Tensorflow.

To enable this use case, Dagster supports customizing the Python environment for each code location by adding the `executable_path` key to the YAML for a location. These environments can involve distinct sets of installed dependencies, or even completely different Python versions. For example:

<CodeExample path="docs_snippets/docs_snippets/concepts/repositories_workspaces/python_environment_example.yaml" />

The example above also illustrates the `location_name` key. Each code location in a workspace file has a unique name that is displayed in the UI, and is also used to disambiguate definitions with the same name across multiple code locations. Dagster will supply a default name for each location based on its workspace entry if a custom one is not supplied.

</TabItem>
</Tabs>

You can see a working example of a Dagster project that has multiple code locations in our [cloud-examples/multi-location-project repo](https://github.com/dagster-io/cloud-examples/tree/main/multi-location-project).
