# Dynamic Partitions Example

This example demonstrates how to use dynamically partitioned assets, through a pipeline that processes data about releases of software project – in this case, the Dagster project itself.

It stores the raw data for each release in the local filesystem, and it stores the release metadata in DuckDB.

Most of the assets in the pipeline are partitioned by release. The final asset, `release_summaries`, is not partitioned because it aggregates over all the releases.

A sensor polls the Github API for new releases. When it finds one, it adds it to the set of partitions and runs the pipeline on it - i.e. requests a materialization of the partition corresponding to that release in each of the assets.

## Getting started

First, copy the project into your working directory:

```bash
dagster project from-example --name assets_dynamic_partitions
```

Then, install the project into your Python environment. By using the --editable flag, pip will install your Python package in ["editable mode"](https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs) so that, as you develop, local code changes will automatically apply.

```bash
pip install -e ".[dev]"
```

Then, start the Dagster web server:

```bash
dagster dev
```

Open http://localhost:3000 with your browser to see the project.

### Environment variables

For the pipeline to be able to pull releases information from Github, you'll need inform it of your Github credentials, via environment variables:

- `GITHUB_USER_NAME`
- `GITHUB_ACCESS_TOKEN` - [instructions on how to make one](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

You can set these environment variables in your terminal. Check out [Using environment variables and secrets guide](https://docs.dagster.io/guides/dagster/using-environment-variables-and-secrets) for info on how to set them in a `.env` file or if you're deploying the pipeline.
