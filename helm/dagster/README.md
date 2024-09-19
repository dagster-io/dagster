# Dagster Helm

[![Artifact HUB](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/dagster)](https://artifacthub.io/packages/search?repo=dagster)

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

### Installing a specific chart version

The `dagster` Python package version and Helm chart version have a 1:1 correspondence, and ideally should
only be used together when the version numbers match.

On installation, we can pass the `--version` flag if a specific chart version is required.

```bash
export VERSION=<DAGSTER_VERSION>
helm install my-release . \
    --namespace dagster \
    --create-namespace \
    --version $VERSION
```

## Introduction

[Dagster](https://github.com/dagster-io/dagster) is a Python library for building data applications. This Helm chart bootstraps a Dagster webserver deployment on a Kubernetes cluster. The chart also supports:

- Deploying user code containers separately from Dagster system components
- Specifying the Dagster run launcher
- Specifying the Dagster scheduler to handle recurring pipeline runs

## Prerequisites

### Setup a Kubernetes Cluster

Please refer to the Kubernetes [getting started guide](https://kubernetes.io/docs/setup/) to set up and run a Kubernetes cluster.

### Install Helm

Helm can be installed by following the [Helm installation guide](https://helm.sh/docs/intro/install/).

### Add Dagster Repo to Helm client

To download and install the Dagster charts, use the following command:

```bash
helm repo add dagster https://dagster-io.github.io/helm
```

We can view the most recent version of the Dagster chart in our chart repository by searching:

```bash
helm search repo dagster
```

To use new releases of the Dagster Helm chart, we'll need to update our chart repository cache.

```bash
helm repo update
```

### Using Helm

We can now use the Helm client to install the Dagster chart! Refer to the guide on [Using Helm](https://helm.sh/docs/intro/using_helm/) for an explanation of useful Helm concepts.

Here we install a release of the Dagster chart named `my-release` under the Kubernetes namespace `dagster`:

```bash
helm install my-release dagster/dagster \
    --namespace dagster \
    --create-namespace
```

### Customizing the Release

[Settings can configured](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing) to customize the Dagster release.

To see the full list of configurable settings, check out the `values.yaml` file. Documentation can be found in the comments.

## Tutorial

For a introductory guide on deploying Dagster with Helm, [check out our documentation](https://docs.dagster.io/deployment/guides/kubernetes/deploying-with-helm).

## Contributing

We cover instructions to get started with developing on our chart.

### JSON Schema

[JSON Schema](https://helm.sh/docs/topics/charts/#schema-files) can impose a structure on our Dagster chart's values to ensure requirement
checks, type validation, range validation, and constraint validation. The Dagster chart's JSON Schema is generated through a Pydantic
model of our values.

```bash
# Install the cli to generate the JSON Schema
pip install -e ./schema

# Display the resulting schema from the Dagster chart values Pydantic model
dagster-helm schema show

# Update the existing schema
dagster-helm schema apply
```

### Template Testing

We use pytest to assert behaviors about our Helm chart.

Helm values are modelled using Pydantic, and then piped through to `helm template`
to generate the chart's Kubernetes manifests. Kubernetes manifests are then transformed into their pythonic object representations,
and assertions are made about these objects to ensure that our templating logic is correct.
