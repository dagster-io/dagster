# {{ repo_name }}

Welcome to your new Dagster repository.

### Contents

| Name | Description |
|-|-|
| `{{ repo_name }}/` | A Python module that contains code for your Dagster repository |
| `{{ repo_name }}_tests/` | A Python module that contains tests for `{{ repo_name }}` |
| `README.md` | A description and guide for this code repository |
| `requirements.txt` | A list of Python package dependencies for this code repository |

## Getting up and running

1. Create a new Python environment and activate.

**Pyenv**
```bash
pyenv virtualenv X.Y.Z {{ repo_name }}
pyenv activate {{ repo_name }}
```

**Conda**
```bash
conda create --name {{ repo_name }}
conda activate {{ repo_name }}
```

2. Once you have activated your Python environment, install the Python dependencies.

```bash
pip install -r requirements.txt
```

## Local Development

1. Start the [Dagit process](https://docs.dagster.io/overview/dagit). This will start a Dagit web
server that, by default, is served on http://localhost:3000.

```bash
dagit -m {{ repo_name }}.repository
```

2. (Optional) If you want to enable Dagster
[Schedules](https://docs.dagster.io/overview/schedules-sensors/schedules) or
[Sensors](https://docs.dagster.io/overview/schedules-sensors/sensors) for your pipelines, start the
[Dagster Daemon process](https://docs.dagster.io/overview/daemon#main) **in a different shell or terminal**:

```bash
dagster-daemon run
```

## Local Testing

Tests can be found in `{{ repo_name }}_tests` and are run with the following command:

```bash
pytest {{ repo_name }}_tests
```

As you create Dagster solids and pipelines, add tests in `{{ repo_name }}_tests/` to check that your
code behaves as desired and does not break over time.

[For hints on how to write tests for solids and pipelines in Dagster,
[see our documentation tutorial on Testing](https://docs.dagster.io/tutorial/testable).
