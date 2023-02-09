# Dagster + dbt starter kit

This starter demonstrates using Python alongside a medium-sized dbt project. It uses dbt's [`jaffle_shop`](https://github.com/dbt-labs/jaffle_shop), [`dagster-dbt`](https://docs.dagster.io/_apidocs/libraries/dagster-dbt), and [DuckDB](https://duckdb.org/).

*New to Dagster? Learn what Dagster is in [Dagster's hands-on Tutorials](https://docs.dagster.io/tutorial) or learn using dbt with Dagster in the [dbt + Dagster tutorial](https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster).*

## Getting started

### Option 1: Deploying it on Dagster Cloud

The easiest way to spin up your Dagster project is to use [Dagster Cloud Serverless](https://docs.dagster.io/dagster-cloud/deployment/serverless). It provides out-of-the-box CI/CD and native branching that make development and deployment easy.

Check out [Dagster Cloud](https://dagster.io/cloud) to get started.

### Option 2: Running it locally

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Then, start the Dagit web server:

```
dagit
```

Open http://localhost:3000 with your browser to see the project.


## Learning more

### Changing the code locally

When developing pipelines locally, be sure to click the **Reload definition** button in the Dagster UI after you change the code. This ensures that Dagster picks up the latest changes you made.

You can reload the code using the **Deployment** page:
<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/images/quickstarts/basic/more-reload-code.png" />
</p>

</details>

Or from the left nav or on each job page:
<details><summary>👈 Expand to view the screenshot</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/images/quickstarts/basic/more-reload-left-nav.png" />
</p>

</details>

### Using environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

Check out [Using environment variables and secrets](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) for more info and examples.

### Running daemon locally

If you're running Dagster locally and trying to set up schedules, you will see a warning that your daemon isn’t running.

<details><summary>👈 Expand to learn how to set up a local daemon</summary>

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/yuhan/11-11-quickstart_1/_add_quickstart_basic_etl_as_the_very_basic_template/docs/next/public/images/quickstarts/basic/step-3-3-daemon-warning.png?raw=true" />
</p>

If you want to enable Dagster [Schedules](https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules) for your jobs, start the [Dagster Daemon](https://docs.dagster.io/deployment/dagster-daemon) process in the same folder as your `workspace.yaml` file, but in a different shell or terminal.

The `$DAGSTER_HOME` environment variable must be set to a directory for the daemon to work. Note: using directories within /tmp may cause issues. See [Dagster Instance default local behavior](https://docs.dagster.io/deployment/dagster-instance#default-local-behavior) for more details.

In this case, go to the project root directory and run:
```bash
dagster-daemon run
```

Once your Dagster Daemon is running, the schedules that are turned on will start running.

<p align="center">
    <img height="500" src="https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/images/quickstarts/basic/step-3-4-daemon-on.png?raw=true" />
</p>

</details>

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Testing

Tests are in the `assets_dbt_python_tests` directory and you can run tests using `pytest`:

```bash
pytest assets_dbt_python_tests
```
