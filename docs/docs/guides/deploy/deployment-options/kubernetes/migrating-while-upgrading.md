---
title: "Migrating a Dagster instance while upgrading Dagster in a Kubernetes environment"
description: We walk through how to migrate your Dagster instance using a Kubernetes Job from the Helm chart.
---

When upgrading your Dagster version, you may also need to migrate your Dagster instance. Migrations will only be required if you are upgrading your minor version.

In this guide, we'll walk you through the migration process in a Kubernetes environment.

## Prerequisites

Before you get started, complete the following:

- **Check the [Dagster migration guide](/guides/migrate/version-migration).** Use the guide to verify any additional steps you may need to take to upgrade your Dagster version.
- **Back up your PostgreSQL database.**

## Step 1: Upgrade the Helm chart

:::note

This article assumes only one release of the Dagster Helm chart is installed in your Kubernetes cluster. All commands should be run in the proper namespace.

:::

1. First, [get the latest information about available charts](https://helm.sh/docs/helm/helm_repo_update/) by running:

   ```shell
   helm repo update
   ```

   This retrieves the latest information about the Dagster Helm chart, which is updated with every Open Source (OSS) release.

2. Run [`helm upgrade`](https://helm.sh/docs/helm/helm_upgrade/) with your desired Dagster chart version and Helm values:

   ```shell
   helm upgrade --install dagster dagster/dagster -f /path/to/values.yaml
   ```

   This installs the new Helm chart and creates a release if it doesn't exist. If it does, the existing `dagster` release will be modified.

## Step 2: Scale down Dagster

Next, you'll scale down the Dagster webserver and daemon deployments. This ensures that there aren't any ongoing job runs writing to the database as the migration happens.

As you scale down the deployments, note each deployment's replica count. You'll use this to scale each one back up after the migration is complete.

```shell
# Get the names of Dagster's webserver and daemon deployments created by Helm
export WEBSERVER_DEPLOYMENT_NAME=`kubectl get deploy \
    --selector=component=dagster-webserver -o jsonpath="{.items[0].metadata.name}"`
export DAEMON_DEPLOYMENT_NAME=`kubectl get deploy \
    --selector=component=dagster-daemon -o jsonpath="{.items[0].metadata.name}"`

# Save each deployment's replica count to scale back up after migrating
export WEBSERVER_DEPLOYMENT_REPLICA_COUNT=`kubectl get deploy \
    --selector=component=dagster-webserver -o jsonpath="{.items[0].status.replicas}"`
export DAEMON_DEPLOYMENT_REPLICA_COUNT=`kubectl get deploy \
    --selector=component=dagster-daemon -o jsonpath="{.items[0].status.replicas}"`

# Scale down the Deployments
kubectl scale deploy $WEBSERVER_DEPLOYMENT_NAME --replicas=0
kubectl scale deploy $DAEMON_DEPLOYMENT_NAME --replicas=0
```

## Step 3: Migrate the Dagster instance

1. Run a Kubernetes job with the `dagster instance migrate` command. In the following example, `helm template` will run a job that uses this command and migrates the instance:

   ```shell
   # Run `helm list` and save your Dagster Helm release name
   export HELM_DAGSTER_RELEASE_NAME=<DAGSTER_RELEASE_NAME>

   # The `helm template` command must be run from the directory containing the
   # `values.yaml` file you used to install the Dagster Helm chart.
   #
   # If needed, you can retrieve the currently applied `values.yaml` file
   # from the cluster by running:
   #
   # `helm get values $HELM_DAGSTER_RELEASE_NAME > values.yaml`
   #
   helm template $HELM_DAGSTER_RELEASE_NAME dagster/dagster \
       --set "migrate.enabled=true" \
       --show-only templates/job-instance-migrate.yaml \
       --values values.yaml \
       | kubectl apply -f -
   ```

2. Next, you'll check that the migration succeeded. Run the following to get the name of the pod:

   ```shell
   kubectl get pods -l job-name=dagster-instance-migrate
   ```

3. Lastly, run the following to inspect the resulting pod, replacing `<POD_NAME>` with the name of the pod:

   ```shell
   kubectl describe pod <POD_NAME>
   ```

   Verify that the pod completed without any errors before proceeding.

## Step 4: Scale Dagster back up

The last step is to scale the Dagster webserver and daemon deployments back up. Run the following commands:

```shell
kubectl scale deploy $WEBSERVER_DEPLOYMENT_NAME --replicas=$WEBSERVER_DEPLOYMENT_REPLICA_COUNT
kubectl scale deploy $DAEMON_DEPLOYMENT_NAME --replicas=$DAEMON_DEPLOYMENT_REPLICA_COUNT
```
