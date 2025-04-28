---
title: 'Retrieve secrets and credentials from Azure Key Vault in AKS'
sidebar_position: 400
---

:::note
This guide is applicable to Dagster+ on AKS only and requires version 1.10.2 or later of the Helm chart.
:::

In this guide, we'll walk through how to retrieve secrets and credentials from Azure Key Vault in an Azure Kubernetes Service (AKS) cluster.
This guide assumes you completed the first step of [Deploying Dagster+ hybrid on Azure](/dagster-plus/deployment/deployment-types/hybrid/azure/aks-agent).

## Prerequisites

To complete the steps in this guide, you'll need:

- The Azure CLI installed on your machine. You can download it [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
- `kubectl` installed on your machine. You can download it [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
- `helm` installed on your machine. You can download it [here](https://helm.sh/docs/intro/install/).
- A functional AKS cluster and Dagster+ agent running on it. If you have not yet set up an AKS agent, you can look up [Deploy an Azure Kubernetes Service (AKS) agent guide](/dagster-plus/deployment/deployment-types/hybrid/azure/aks-agent).

## Step 1: Enable the Azure Key Vault provider for the AKS cluster

To deploy the AKS Secrets store CSI drivers and providers, run the following command:

```bash
az aks enable-addons --resource-group <resource-group> --name <cluster-name> --addons azure-keyvault-secrets-provider
```

You can validate that both components are running by checking the pods in the `kube-system` namespace:

```bash
kubectl get pods -n kube-system -l 'app in (secrets-store-csi-driver,secrets-store-provider-azure)' -o wide
```

Each node should have a pod of `aks-secrets-store-csi-driver` and `secrets-store-provider-azure` running.

## Step 2: Create an Azure Key Vault

Create the Azure Key Vault with RBAC authorization enabled:

```bash
az keyvault create -n <vault-name> -g <resource-group> --enable-rbac-authorization
```

Add yourself with the role to manage the keys in the secret vault:

```bash
az role assignment create --role 'Key Vault Administrator' --assignee '<your identity>' --scope '/subscriptions/<subscription_id>/resourceGroups/<resource_group>'
```

## Step 3: Store the Dagster Cloud Agent Token in the Key Vault

Grant the AKS cluster access to the Key Vault:

```bash
export CLIENT_ID=$(az identity show -g <resource-group> -n <agent-identity> --query 'clientId' -otsv)
export KEYVAULT_SCOPE=$(az keyvault show --name <vault-name> --query id -o tsv)
az role assignment create --role "Key Vault Secrets User" --assignee $CLIENT_ID --scope $KEYVAULT_SCOPE
```

See the [Azure built-in roles for Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/general/rbac-guide?tabs=azure-cli#azure-built-in-roles-for-key-vault-data-plane-operations).

## Step 4: Create and access the Dagster Cloud Agent Token from your Key Vault

Create a secret in the Azure Key Vault to store the Dagster Cloud Agent Token:

```bash
az keyvault secret set --name dagsterAgentToken --vault-name <vault-name> --value <dagster-token>
```

Create the secret provider class to retrieve the secret from the Key Vault:

```bash
export CLIENT_ID=$(az identity show -g <resource-group> -n <agent-identity> --query 'clientId' -otsv)
export KEYVAULT_NAME=<vault-name>
export IDENTITY_TENANT=$(az aks show --name <aks-cluster> --resource-group <resource-group> --query identity.tenantId -o tsv)

# write the secret provider manifest to a file
cat <<EOF > dagster-token-secret-provider.yaml
# This is a SecretProviderClass example using workload identity to access your key vault
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-kv-dagster-agent-token # needs to be unique per namespace
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    clientID: "${CLIENT_ID}" # Setting this to use workload identity
    keyvaultName: ${KEYVAULT_NAME}       # Set to the name of your key vault
    cloudName: ""                         # [OPTIONAL for Azure] if not provided, the Azure environment defaults to AzurePublicCloud
    objects:  |
      array:
        - |
          objectName: dagsterAgentToken   # Set to the name of your secret
          objectType: secret              # object types: secret, key, or cert
          objectVersion: ""               # [OPTIONAL] object versions, default to latest if empty
    tenantId: "${IDENTITY_TENANT}"        # The tenant ID of the key vault
  # (optional) Allows mounting the secret as an environment variable in a pod
  secretObjects:
  - data:
    - key: dagsterAgentToken
      objectName: dagsterAgentToken
    secretName: dagster
    type: Opaque
EOF

# apply the secret provider manifest
kubectl apply -f dagster-token-secret-provider.yaml
```

You can verify that the secret provider is working by creating a pod that uses the secret provider.

This example provides three ways of exposing a secret in a pod.

```bash
cat <<EOF > pod-test-akv-secret-mount.yaml
kind: Pod
apiVersion: v1
metadata:
  name: test-akv-secret-mount
  labels:
    azure.workload.identity/use: "true"
spec:
  serviceAccountName: "user-cloud-dagster-cloud-agent"
  containers:
    - name: busybox
      image: registry.k8s.io/e2e-test-images/busybox:1.29-4
      command:
        - "/bin/sleep"
        - "10000"
      # This will mount the secret as /mnt/secrets-store/dagsterAgentToken
      volumeMounts:
      - name: secrets-store01-inline
        mountPath: "/mnt/secrets-store"
        readOnly: true
      # This will expose the secret as an environment variable named DAGSTER_CLOUD_AGENT_TOKEN
      env:
      - name: DAGSTER_CLOUD_AGENT_TOKEN
        valueFrom:
          secretKeyRef:
            name: dagster
            key: dagsterAgentToken
      # This will expose all the secrets from the secret provider as environment variables name as the secret names
      envFrom:
      - secretRef:
          name: dagster
  volumes:
    - name: secrets-store01-inline
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: "azure-kv-dagster-agent-token"
EOF

# Create the test pod
kubectl apply -f pod-test-akv-secret-mount.yaml

# Each of these commands should print value of the secret
kubectl exec -it test-akv-secret-mount -- cat /mnt/secrets-store/dagsterAgentToken
kubectl exec -it test-akv-secret-mount -- echo $DAGSTER_CLOUD_AGENT_TOKEN
kubectl exec -it test-akv-secret-mount -- echo $dagsterAgentToken

# clean up
kubectl delete pod test-akv-secret-mount
```

## Step 5: Modify your AKS deployment to use the Dagster+ token from the Key Vault

Modify the following sections of your values.yaml file.

a) update the `dagsterCloud` section:

This will ensure the agent token is provided and expected as the environment variable `dagsterAgentToken`.

```yaml
dagsterCloud:
  agentTokenSecretName: dagster
  agentTokenEnvVarName: dagsterAgentToken
  # ...
```

b) add these entries to the `dagsterCloudAgent` section:

Required for the csi driver to mount the secret into the agent pod.

```yaml
dagsterCloudAgent:
  volumeMounts:
    - name: dagster-token
      mountPath: /mnt/dagster-token
      readOnly: true
  volumes:
    - name: dagster-token
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: 'azure-kv-dagster-agent-token'
```

c) add these entries to the `workspace`:

This ensures the secret is also made available to the pods the agent will create to run your code.

```yaml
envSecrets:
  - name: dagster
    optional: false
volumeMounts:
  - name: dagster-token
    mountPath: /mnt/dagster-token
    readOnly: true
volumes:
  - name: dagster-token
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: 'azure-kv-dagster-agent-token'
```

d) optionally, you could manage the secret provider within your helm values file by providing it as an extra manifest, instead of provisioning it separately:

```yaml
extraManifests:
  # This is a SecretProviderClass example using workload identity to access your key vault
  - apiVersion: secrets-store.csi.x-k8s.io/v1
    kind: SecretProviderClass
    metadata:
      name: azure-kv-dagster-agent-token # needs to be unique per namespace
    spec:
      provider: azure
      parameters:
        usePodIdentity: 'false'
        clientID: '${CLIENT_ID}' # Setting this to use workload identity
        keyvaultName: ${KEYVAULT_NAME} # Set to the name of your key vault
        cloudName: '' # [OPTIONAL for Azure] if not provided, the Azure environment defaults to AzurePublicCloud
        objects: |
          array:
            - |
              objectName: dagsterAgentToken   # Set to the name of your secret
              objectType: secret              # object types: secret, key, or cert
              objectVersion: ""               # [OPTIONAL] object versions, default to latest if empty
        tenantId: '${IDENTITY_TENANT}' # The tenant ID of the key vault
      # (optional) Allows mounting the secret as an environment variable in a pod
      secretObjects:
        - data:
            - key: dagsterAgentToken
              objectName: dagsterAgentToken
          secretName: dagster
          type: Opaque
```

Finally, update your deployment with the new values:

```bash
helm upgrade -n <dagster-namespace> user-cloud dagster-cloud/dagster-cloud-agent -f ./values.yaml
```

You can verify that the agent is running by looking at its status in the Dagster+ UI at this address:

`https://<org_name>.dagster.plus/<deployment>/deployment/health`

:::tip

By re-using the same steps to create other secret provider, volume mounts, and optionally environment variables configuration,
you can also load other secrets and credentials from the Azure Key Vault to use in your Dagster+ code projects.

:::
