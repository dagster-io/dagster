---
description: Deploy a Dagster+ hybrid agent on Azure Container Apps, without running a Kubernetes cluster.
sidebar_position: 5500
title: Deploy a Dagster+ agent on Azure Container Apps
tags: [dagster-plus-feature]
---

:::note

This guide is applicable to Dagster+. The Azure Container Apps agent is in beta.

:::

In this guide, you'll deploy a Dagster+ hybrid agent on [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/). Container Apps is Microsoft's managed container service. It runs containers for you without a Kubernetes cluster to operate, similar to Amazon Elastic Container Service (ECS) on Fargate.

The agent runs as a long-lived Container App. Each code location runs as its own Container App, and each Dagster run executes as a short-lived Container Apps Job that exits when the run finishes.

If you prefer to run on Azure Kubernetes Service (AKS), see the [AKS agent guide](/deployment/dagster-plus/hybrid/azure/aks-agent) instead.

## Prerequisites

To complete the steps in this guide, you'll need:

- **In Dagster+:**
  - **Organization Admin** permissions in your organization.
  - A hybrid deployment. See [Getting started with hybrid deployment](/deployment/dagster-plus/hybrid).
  - An agent token. See [Managing agent tokens](/deployment/dagster-plus/management/tokens/agent-tokens).
- **In Azure:**
  - A subscription and a resource group for the agent.
  - Permission to create role assignments in that resource group: the **Owner** or **User Access Administrator** role. The template grants the agent's identity the rights it needs, and plain **Contributor** cannot do that.
  - An [Azure Container Registry (ACR)](https://learn.microsoft.com/azure/container-registry/) in the same resource group, for your code location images.
  - The [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), signed in with `az login`.

## Step 1: Deploy the agent

We provide a template that creates everything the agent needs: a virtual network, an Azure Key Vault that holds the agent token, a managed identity the agent runs as, a Log Analytics workspace, a Container Apps environment, and the agent itself.

Deploy it into your resource group with the Azure CLI. Replace the values in angle brackets. The last parameter looks up your registry's id so the template can grant the agent permission to pull from it.

```shell
az deployment group create \
  --resource-group <resource-group> \
  --template-uri https://s3.amazonaws.com/dagster.cloud/azure/full-stack-template.json \
  --parameters \
    dagsterOrgId=<your-organization> \
    dagsterDeploymentName=<your-deployment> \
    dagsterCloudApiTokenSecretName=dagster-agent-token \
    dagsterCloudApiToken=<your-agent-token> \
    acrResourceId=$(az acr show --name <your-registry> --query id --output tsv)
```

A few parameters worth knowing:

| Parameter                                         | What it does                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agentImage`                                      | Defaults to the `dagster-cloud-agent` image matching the template's release. Override only to pin a different version or use your own build.                                                                                                                                                                                                                                      |
| `keyVaultName`                                    | Defaults to a name derived from your subscription and resource group, so redeploying into the same group reuses it. Key Vault names must be unique across all of Azure, and a deleted vault keeps its name for 90 days: if you are reinstalling into a group you deleted, purge the old vault first (see [Removing the deployment](#removing-the-deployment)) or pass a new name. |
| `acrResourceId`                                   | Grants the agent's identity permission to pull images from your registry. Code locations and run workers pull with that identity, so you never store registry passwords.                                                                                                                                                                                                          |
| `agentMetricsEnabled`, `codeServerMetricsEnabled` | Report CPU and memory usage to Dagster+. Off by default.                                                                                                                                                                                                                                                                                                                          |
| `runJobReplicaTimeout`                            | How long a run is allowed to execute before Azure stops it, in seconds. Defaults to 24 hours.                                                                                                                                                                                                                                                                                     |
| `dagsterRegion`                                   | Set to `eu` for organizations in the Dagster+ EU region.                                                                                                                                                                                                                                                                                                                          |
| `enableResourceLocks`                             | On by default. Puts delete locks on the Key Vault and the agent's identity so they can't be removed by accident. See [Removing the deployment](#removing-the-deployment).                                                                                                                                                                                                         |

The deployment takes 15 to 20 minutes. Most of that is Azure creating the Container Apps environment.

When it finishes, the agent appears on the **Agents** tab of your deployment in Dagster+ with status **Running**.

## Step 2: Publish a code location image

Build your code location as a Docker image that includes `dagster` and `dagster-cloud`, and push it to your registry. If you don't run Docker locally, the registry can build it for you:

```shell
az acr build --registry <your-registry> --image my-location:1 .
```

For details on structuring the image, see [Deploying user code in ACR](/deployment/dagster-plus/hybrid/azure/acr-user-code).

## Step 3: Add the code location

Add the location to your deployment with the image you pushed:

```yaml title="dagster_cloud.yaml"
locations:
  - location_name: my-location
    image: <your-registry>.azurecr.io/my-location:1
    code_source:
      module_name: my_location.definitions
```

```shell
dagster-cloud workspace add-location my-location --from dagster_cloud.yaml \
  --url https://<your-organization>.dagster.cloud \
  --deployment <your-deployment> \
  --api-token <your-user-token>
```

`add-location` adds or updates only the named location. `dagster-cloud workspace sync` also works, but it removes any location in the deployment that is not in the file.

Within a couple of minutes the location loads in Dagster+, and a Container App named after the location appears in your resource group. Launch a run; a Container Apps Job named after the run id (`dagster-run-...`) appears alongside it, and the run's logs stream to Dagster+.

## Configuration reference

### Agent settings

The template writes these into the agent's `dagster.yaml`. If you run the agent yourself, configure the launcher directly:

```yaml title="dagster.yaml"
user_code_launcher:
  module: dagster_cloud.workspace.aca.launcher
  class: AcaUserCodeLauncher
  config:
    subscription_id: <subscription-id>
    resource_group: <resource-group>
    environment_name: <container-apps-environment>
    region: eastus
    identity_id: <managed-identity-resource-id>
    server_resources:
      cpu: '0.5'
      memory: '1Gi'
    run_resources:
      cpu: '1'
      memory: '2Gi'
    run_job_replica_timeout: 86400
    agent_metrics:
      enabled: true
    code_server_metrics:
      enabled: true
```

| Setting                                                           | Description                                                                                                                                   |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `subscription_id`, `resource_group`, `environment_name`, `region` | Where code servers and run Jobs are created.                                                                                                  |
| `identity_id`                                                     | The managed identity attached to code servers and run Jobs. Used to pull images from Azure Container Registry.                                |
| `server_resources`                                                | CPU and memory for each code server. CPU accepts cores (`"0.5"`) or millicores (`"500m"`).                                                    |
| `run_resources`                                                   | CPU and memory for each run worker.                                                                                                           |
| `run_job_replica_timeout`                                         | Seconds a run may execute before Azure stops it. Azure requires a finite value.                                                               |
| `env_vars`                                                        | Environment variables to pass to code servers and run workers. `KEY=value` sets a value; a bare `KEY` copies it from the agent's environment. |

### Per-code-location settings

Override run resources or environment variables for one location in `dagster_cloud.yaml`:

```yaml title="dagster_cloud.yaml"
locations:
  - location_name: my-location
    image: <your-registry>.azurecr.io/my-location:1
    code_source:
      module_name: my_location.definitions
    container_context:
      aca:
        run_resources:
          cpu: '2'
          memory: '4Gi'
        env_vars:
          - MY_SETTING=value
```

### Limiting the agent's Azure permissions

By default the template gives the agent's identity the built-in **Contributor** role on the resource group, which lets it change anything in the group. If you would rather allow only the operations the agent performs (creating, starting, stopping, and deleting Container Apps and Jobs), create our [custom role](https://learn.microsoft.com/azure/role-based-access-control/custom-roles) once per subscription and pass its id to the template. The `--query ... -o tsv` part prints only the new role's id so it can be captured in a variable; `--location` is where Azure records the deployment, not where anything runs:

```bash
ROLE_ID=$(az deployment sub create --location <region> \
  --template-uri https://s3.amazonaws.com/dagster.cloud/azure/aca-agent-role.json \
  --query properties.outputs.roleDefinitionId.value -o tsv)
az deployment group create ... --parameters agentRoleDefinitionId=$ROLE_ID
```

Creating a custom role requires **Owner** or **User Access Administrator** on the subscription.

If the agent was first deployed with the default **Contributor** role, redeploying with the custom role adds the new assignment but cannot remove the old one. Remove it yourself so the agent is actually limited:

```bash
az role assignment delete --resource-group <resource-group> --role Contributor \
  --assignee $(az identity show --resource-group <resource-group> --name dagster-agent-identity --query principalId -o tsv)
```

After changing which role the agent has, or what a custom role grants, [restart the agent's revision](https://learn.microsoft.com/azure/container-apps/revisions-manage#restart). The nested command looks up the name of the currently running revision:

```bash
az containerapp revision restart --resource-group <resource-group> --name dagster-aca-agent \
  --revision $(az containerapp show -g <resource-group> -n dagster-aca-agent --query properties.latestReadyRevisionName -o tsv)
```

Azure keeps serving an identity's previous permissions for several minutes after a role change (see [role assignment changes are not being detected](https://learn.microsoft.com/azure/role-based-access-control/troubleshooting#symptom---role-assignment-changes-are-not-being-detected)), and the running agent does not notice the update on its own. Until it restarts, launches can fail with `AuthorizationFailed`. This differs from the ECS and Kubernetes agents, where permission changes take effect on the next request.

## Logs, metrics, and alerts

- **Run logs:** appear in Dagster+ as usual. The run worker's raw stdout and stderr are also available under the run's **Raw compute logs** tab.
- **Agent and code server logs:** written to the Log Analytics workspace the template creates, in the `ContainerAppConsoleLogs_CL` table, keyed by Container App name. Run worker output lands there too, keyed by the Job execution name in the `ContainerGroupName_s` column, though the run's compute logs in Dagster+ are the easier place to read it.
- **Metrics:** with `agentMetricsEnabled` and `codeServerMetricsEnabled` on, the agent reports its own and each code server's CPU and memory usage, visible on the **Agents** tab and per code location.
- **Alerts:** the template can create Azure Monitor alerts for agent restarts and Key Vault access failures. Set `enableAlerts=true` and `alertEmailAddress`. Dagster+ agent-unavailable alerts work the same way as for any other agent type.

## Limitations

- Runs start slowly compared with Kubernetes or ECS: expect about 90 seconds from launch to the first step, because each run is a new Container Apps Job that Azure has to create and start. The agent also hands launches to Azure one at a time, so runs launched together start roughly 30 seconds apart. Schedules that fire many runs in the same minute will see them stagger; the runs execute concurrently once started.
- If a run worker is killed from outside Dagster, the agent's health check marks the run failed within about a minute.
- Each Container Apps environment allows 200 Container Apps. Completed run Jobs do not count toward that, but each code location does.
- Volume mounts are not supported yet. Disk space cannot be requested directly on Container Apps: each container gets ephemeral scratch storage sized by its CPU allocation, roughly 4 GiB per vCPU, so raise `run_resources.cpu` if a run needs more local disk. See [Azure's storage mount documentation](https://learn.microsoft.com/azure/container-apps/storage-mounts) for the exact limits.
- Re-running the template updates the agent in place. Old agent revisions are retired automatically unless you set `enableZeroDowntimeDeploys=true`, in which case you must deactivate them yourself.
- Completed Jobs are left in the resource group as metadata and cost nothing; terminated runs have their Job deleted.

## Removing the deployment

The template locks the Key Vault and the agent's identity against deletion by default, and Azure refuses to delete a resource group that contains a locked resource. Remove the locks, then delete the group:

```bash
az lock delete --ids $(az lock list --resource-group <resource-group> --query "[].id" -o tsv)
az group delete --name <resource-group> --yes --no-wait
```

Expect the deletion to take about half an hour. Nearly all of that is Azure tearing down the [Container Apps environment](https://learn.microsoft.com/azure/container-apps/environment) and releasing the [subnet it was integrated with](https://learn.microsoft.com/azure/container-apps/custom-virtual-networks); the other resources go in a minute or two. The resource group stays in a `Deleting` state the whole time, and a new deployment into a group of the same name fails with `ResourceGroupBeingDeleted` until it is gone.

The Key Vault is [soft-deleted](https://learn.microsoft.com/azure/key-vault/general/soft-delete-overview) and keeps its name reserved for 90 days. The default vault name depends only on the subscription and group name, so reinstalling into a group with the same name fails with a conflict on the vault until you purge it after the group is gone:

```bash
az keyvault purge --name <key-vault-name>
```
