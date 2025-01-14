---
title: dagster_cloud.yaml reference
sidebar_position: 200
---

:::note
This reference is applicable to Dagster+.
:::

`dagster_cloud.yaml` is used to define multiple code locations for Dagster+. It is similar to `workspace.yaml` in Dagster open source. For [Hybrid deployments](/dagster-plus/deployment/deployment-types/hybrid/), `dagster_cloud.yaml` can be used to manage environment variables and secrets.


## File location

The `dagster_cloud.yaml` file should be placed in the root of your Dagster project, similar to the example below:

```shell
example_etl
├── README.md
├── example_etl
│   ├── __init__.py
│   ├── assets
│   ├── docker_image
├── ml_project
│   ├── example_ml
│     ├── __init__.py
│     ├── ml_assets
├── random_assets.py
├── example_etl_tests
├── dagster_cloud.yaml
├── pyproject.toml
├── setup.cfg
└── setup.py
```

If your repository contains multiple Dagster projects in subdirectories - otherwise known as a monorepository - add the `dagster_cloud.yaml` file to the root of where the Dagster projects are stored.

## File structure

Settings are formatted using YAML. For example, using the file structure above as an example:

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    build:
      directory: ./example_etl
      registry: localhost:5000/docker_image
  - location_name: ml-pipeline
    code_source:
      package_name: example_ml
    working_directory: ./ml_project
    executable_path: venvs/path/to/ml_tensorflow/bin/python
  - location_name: my_random_assets
    code_source:
      python_file: random_assets.py
    container_context:
      k8s:
        env_vars:
          - database_name
          - database_username=hooli_testing
        env_secrets:
          - database_password
```

## Settings

The `dagster_cloud.yaml` file contains a single top-level key, `locations`. This key accepts a list of code locations; for each code location, you can configure the following:

- [Location name](#location-name)
- [Code source](#code-source)
- [Working directory](#working-directory)
- [Build](#build)
- [Python executable](#python-executable)
- [Container context](#container-context)

### Location name

**This key is required.** The `location_name` key specifies the name of the code location. The location name will always be paired with a [code source](#code-source).

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
```

| Property        | Description                                                                            | Format   |
|-----------------|----------------------------------------------------------------------------------------|----------|
| `location_name` | The name of your code location that will appear in the Dagster UI Code locations page. | `string` |

### Code source

**This section is required.** The `code_source` defines how a code location is sourced.

A `code_source` key must contain either a `module_name`, `package_name`, or `file_name` parameter that specifies where to find the definitions in the code location.

<Tabs>
<TabItem value="Single code location">

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
```

</TabItem>
<TabItem value="Multiple code locations">

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
  - location_name: machine_learning
    code_source:
      python_file: ml/ml_model.py
```

</TabItem>
</Tabs>

| Property                   | Description                                                                       | Format                   |
|----------------------------|-----------------------------------------------------------------------------------|--------------------------|
| `code_source.package_name` | The name of a package containing Dagster code                                     | `string` (folder name)   |
| `code_source.python_file`  | The name of a Python file containing Dagster code (e.g. `analytics_pipeline.py` ) | `string` (.py file name) |
| `code_source.module_name`  | The name of a Python module containing Dagster code (e.g. `analytics_etl`)        | `string` (module name)   |

### Working directory

Use the `working_directory` setting to load Dagster code from a different directory than the root of your code repository. This setting allows you to specify the directory you want to load your code from.

Consider the following project:

```shell
example_etl
├── README.md
├── project_directory
│   ├── example_etl
│     ├── __init__.py
│     ├── assets
│   ├── example_etl_tests
├── dagster_cloud.yaml
├── pyproject.toml
├── setup.cfg
└── setup.py
```

To load from `/project_directory`, the `dagster_cloud.yaml` code location would look like this:

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    working_directory: ./project_directory
```

| Property            | Description                                                             | Format          |
|---------------------|-------------------------------------------------------------------------|-----------------|
| `working_directory` | The path of the directory that Dagster should load the code source from | `string` (path) |

### Build

The `build` section contains two parameters:

- `directory` - Setting a build directory is useful if your `setup.py` or `requirements.txt` is in a subdirectory instead of the project root. This is common if you have multiple Python modules within a single Dagster project.
- `registry` - **Applicable only to Hybrid deployments.** Specifies the Docker registry to push the code location to.

In the example below, the Docker image for the code location is in the root directory and the registry and image defined:

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    build:
      directory: ./
      registry: your-docker-image-registry/image-name # e.g. localhost:5000/myimage
```


| Property          | Description                                                                                                                                                           | Format                     | Default |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------|---------|
| `build.directory` | The path to the directory in your project that you want to deploy. If there are subdirectories, you can specify the path to only deploy a specific project directory. | `string` (path)            | `.`     |
| `build.registry`  | **Applicable to Hybrid deployments.** The Docker registry to push your code location to                                                                               | `string` (docker registry) |         |


### Python executable

For Dagster+ Hybrid deployments, the Python executable that is installed globally in the image, or the default Python executable on the local system if you use the local agent, will be used. To use a different Python executable, specify it using the `executable_path` setting. It can be useful to have different Python executables for different code locations.

{/* For Dagster+ Serverless deployments, you can specify a different Python version by [following these instructions](/dagster-plus/deployment/deployment-types/serverless/runtime-environment#python-version). */}
For Dagster+ Serverless deployments, you can specify a different Python version by [following these instructions](/todo).

```yaml
# dagster_cloud.yaml

locations:
  - location_name: data-eng-pipeline
    code_source:
      package_name: example_etl
    executable_path: venvs/path/to/dataengineering_spark_team/bin/python
  - location_name: machine_learning
    code_source:
      python_file: ml_model.py
    executable_path: venvs/path/to/ml_tensorflow/bin/python
```

| Property          | Description                                   | Format          |
|-------------------|-----------------------------------------------|-----------------|
| `executable_path` | The file path of the Python executable to use | `string` (path) |

### Container context

If using Hybrid deployment, you can define additional configuration options for code locations using the `container_context` parameter. Depending on the Hybrid agent you're using, the configuration settings under `container_context` will vary.

Refer to the configuration reference for your agent for more info:

{/* - [Docker agent configuration reference](/dagster-plus/deployment/agents/docker/configuration-reference) */}
- [Docker agent configuration reference](/todo)
{/* - [Amazon ECS agent configuration reference](/dagster-plus/deployment/agents/amazon-ecs/configuration-reference) */}
- [Amazon ECS agent configuration reference](/todo)
{/* - [Kubernetes agent configuration reference](/dagster-plus/deployment/agents/kubernetes/configuration-reference) */}
- [Kubernetes agent configuration reference](/todo)
