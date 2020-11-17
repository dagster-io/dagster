# Dagster Helm

## TL;DR

### Installing from remote
```bash
helm repo add dagster https://dagster-io.github.io/helm

helm install my-release dagster/dagster \
    --namespace dagster \
    --create-namespace
```

### Installing from source
```bash
helm install my-release . \
    --namespace dagster \
    --create-namespace
```
## Introduction
[Dagster](https://github.com/dagster-io/dagster) is a Python library for building data applications. This chart will bootstrap a Dagit web server deployment on a Kubernetes cluster using the Helm package manager.

In addition, our helm chart allows for Dagster configuration such as:
 - Deploying user code containers separately from Dagster system components
 - Specifying the Dagster run launcher
 - Specifying the Dagster scheduler to handle recurring pipeline runs

## Prerequisites
### Setup a Kubernetes Cluster
Please refer to the Kubernetes [getting started guide](https://kubernetes.io/docs/setup/) to set up and run a Kubernetes cluster.

### Installing Helm
We use Helm to manage our Kubernetes application in a configurable, replicable, and sharable way. Helm can be installed by following the [Helm installation guide](https://helm.sh/docs/intro/install/).

### Adding the Dagster Repo
To download and install the Dagster charts, use the following command:

```bash
helm repo add dagster https://dagster-io.github.io/helm
```

### Using Helm
We can now use the Helm client to install the Dagster chart! Refer to the guide on [Using Helm](https://helm.sh/docs/intro/using_helm/) for an explanation of useful Helm concepts.

Here, we install a release of the Dagster chart named `my-release`, under the Kubernetes namespace `dagster`:

```bash
helm install my-release dagster/dagster \
    --namespace dagster \
    --create-namespace
```

### Customizing the Release
[Settings can configured](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing) to customize the Dagster release.

To see the full list of configurable settings, check out the `values.yaml` file. Documentation can be found in the comments.
## Environment Variables

We support two ways of setting environment variables: either directly add them to `values.yaml`, or
provide an external ConfigMap/Secret object to mount using `envFrom:` in the chart pods:

- `job_runner.env.SOME_ENV_VAR`: Set `SOME_ENV_VAR` in the Celery Worker and Job pods
- `dagit.env.SOME_ENV_VAR`: Set `SOME_ENV_VAR` in the Dagit pod
- `job_runner.env_config_maps`: names of ConfigMaps to use for environment variables in the
  Celery Worker and Job pods
- `job_runner.env_secrets`: names of Secrets to use for environment variables in the
  Celery Worker and Job pods
- `dagit.env_config_maps`: names of ConfigMaps to use for environment variables in the Dagit pod
- `dagit.env_secrets`: names of Secrets to use for environment variables in the Dagit pod

These will be loaded in the following order, and in the case of conflicts, subsequent loads will
take priority:

1. Base environment; custom env vars specified in `values.yaml`
2. ConfigMap environment variables, loaded in order of the ConfigMaps specified
3. Secret environment variables, loaded in order of the Secrets specified

Thus, for example, if `CUSTOM_ENV_VAR` appears in `values.yaml`, a ConfigMap, and two secrets, the
last secret loaded will be the value of `CUSTOM_ENV_VAR` at runtime.

### Implementation Notes

This chart installs a base pair of Kubernetes ConfigMap objects for environment variables. These
are:

- `dagster-job-runner-env`: Environment variables for the Celery workers and the spawned Job pod
- `dagster-dagit-env`: Environment variables for the Dagit Deployment pod

Each of these ConfigMaps set `DAGSTER_HOME` by default, and also enable user-specification of
additional environment variables directly in `values.yaml`.

Additionally, this Helm chart supports pulling in other external environment variables from external
Kubernetes ConfigMaps and Secrets.
