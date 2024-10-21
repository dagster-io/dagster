# Workspace File Reference

:::info
    This reference is only applicable to Dagster OSS, for Dagster Cloud see [the Dagster Cloud Code Locations guide](/dagster-plus/deployment/code-locations)
:::

The `workspace.yaml` file is used to configure code locations in Dagster. It tells Dagster where to find your code and how to load it.

## Location of workspace.yaml

Dagster command-line tools (like dagster dev, dagster-webserver, or dagster-daemon run) look for workspace files in the current directory when invoked. This allows you to launch from that directory without the need for command line arguments

To load the workspace.yaml file from a different folder, use the -w argument:

```bash
dagster dev -w path/to/workspace.yaml
```

## File Structure

The `workspace.yaml` file uses the following structure:

```yaml
load_from:
  - <loading_method>:
      <configuration_options>
```

Where `<loading_method>` can be one of:
- `python_file`
- `python_module`
- `grpc_server`



## Loading Methods

We recommend using `python_module` for most use cases.

### Python module

Loads a code location from a Python module.

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

Loads a code location from a Python file.

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
      location_name: "my_grpc_server"
```

## Multiple Code Locations

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

## Notes

- Each code location is loaded in its own process.
- Code locations can mix and match between `Definitions` objects and `@repository` decorators.
- If a code location is renamed or its configuration is modified, running schedules and sensors in that location need to be stopped and restarted.