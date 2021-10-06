# Hacker News Demo Jobs - Software-Defined Assets Version

This repo used Dagster's experimental software-defined asset APIs to set up a "realistic" example of using dagster in a production world, integrating with
many of its features, including:

- Schedules / Sensors
- Asset Materializations
- IOManagers
- Resources
- Unit Tests
- dbt, snowflake, s3, and pyspark integrations

Feel free to poke around!

#### Note:

Running these jobs for yourself without modifications would be pretty tricky, as many of these
solids and resources are configured for a specific environment, and make use of environment
variables that you will not have set on your machine. This is intended as a point of reference
demonstrating the structure of a more advanced Dagster repo.

## High Level Overview

This repo contains three jobs:

- `hacker_news_api_download`
  - This job downloads events from the Hacker News API, splits them by type, and stores comments
    and stories into their own seperate tables in our Snowflake database.
- `story_recommender`
  - This job reads from the tables that `hacker_news_api_download` writes to, and uses this data
    to train a machine learning model to recommend stories to specific users based on their comment history.
- `dbt_metrics`
  - This job also uses the tables that the `hacker_news_api_download` produces, this time running a dbt
    project which consumes them and creates aggregated metric tables.

The `hacker_news_api_download` job runs on an hourly schedule, constantly updating the tables with new data.
The `story_recommender` job is triggered by a sensor, which detects when both of its input tables have been updated.
The `dbt_metrics` job is triggered by a different sensor, which will fire a run whenever `hacker_news_api_download` finishes.

Each job makes use of resources, which allows data to be read from and written to different locations based on the environment.

## Deploying

The instructions below show you how to deploy this repository to a Dagster deployment in a Kubernetes cluster.

You'll need access to Snowflake credentials, AWS credentials, and a Slack API token.

- Build an image using the Dockerfile in this folder.

```
docker build . -t hacker-news:test
```

- Tag the image and push it to a Docker registry. For example, in ECR:

```
docker tag hacker-news:test <your aws account>.dkr.ecr.us-west-2.amazonaws.com/hacker-news:test
docker push <your aws account>.dkr.ecr.us-west-2.amazonaws.com/hacker-news:test
```

- Create secrets in your k8s cluster containing values for the following environment variables:

```
# AWS credentials
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCOUNT_ID
AWS_DEFAULT_REGION

# Snowflake credentials
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD

# Slack API token
SLACK_DAGSTER_ETL_BOT_TOKEN
```

- Follow the instructions in our [Helm chart documentation](https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm) for deploying a user code deployment.

The relevant part of your Helm `values.yaml` that loads the `hacker_news` package might look like:

```
dagster-user-deployments:
  enabled: true
  deployments:
    - name: "hacker-news-example"
      image:
        repository: <your aws account>.dkr.ecr.us-west-2.amazonaws.com/hacker-news
        tag: test
        pullPolicy: Always
      dagsterApiGrpcArgs:
        - "--package-name"
        - "hacker-news"
      port: 3030
      envSecrets:
        - name: your-aws-secret-name
        - name: your-snowflake-secret-name
        - name: your-slack-secret-name

runLauncher:
  type: K8sRunLauncher
  config:
    k8sRunLauncher:
      envSecrets:
        - name: your-aws-secret-name
        - name: your-snowflake-secret-name
        - name: your-slack-secret-name
```
