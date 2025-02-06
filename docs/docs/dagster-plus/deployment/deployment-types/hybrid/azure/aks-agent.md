---
title: "Deploy a Dagster+ agent on an Azure Kubernetes Service cluster"
sidebar_position: 100
---

This guide will walk you through deploying a Dagster+ agent on an Azure Kubernetes Service (AKS) cluster.

This guide is intended to be a quickstart, and you should always defer to organization-specific guidelines for creating and managing new infrastructure.

We'll start from a brand new organization in Dagster+, and finish with a full hybrid deployment of Dagster+ using Azure infrastructure.

## Prerequisites

To complete the steps in this guide, you'll need:

- The azure CLI installed on your machine. You can download it [here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
- `kubectl` installed on your machine. You can download it [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/).
- `helm` installed on your machine. You can download it [here](https://helm.sh/docs/intro/install/).
- An existing AKS cluster. If you need to create a new AKS cluster, refer to the [Azure documentation](https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli).
- A Dagster+ organization, with an agent token for that organization.

## Step 1: Generate a Dagster+ agent token.

In this step, you'll generate a token for the Dagster+ agent. The Dagster+ agent will use this to authenticate to the agent API.

1. Sign in to your Dagster+ instance.
2. Click the **user menu (your icon) > Organization Settings**.
3. In the **Organization Settings** page, click the **Tokens** tab.
4. Click the **+ Create agent token** button.
5. After the token has been created, click **Reveal token**.

Keep the token somewhere handy - you'll need it to complete the setup.

## Step 2: Log in to your AKS cluster.

We'll use the `azure` CLI to log in to your AKS cluster. Run the following command and follow the prompts to log in:

```bash
az login
az aks get-credentials --resource-group <your-resource-group> --name <your-aks-cluster>
```

We should now be able to verify our installation by running a command that tells us the current context of our kubectl installation. We'd expect it to output the name of the AKS cluster.

```bash
kubectl config current-context
```

## Step 3: Install the Dagster+ agent on the AKS cluster.

Next, we'll install the agent helm chart. You should be able to follow the guide [here](/dagster-plus/deployment/deployment-types/hybrid/kubernetes/configuration) to install the agent on the AKS cluster.

## Next steps

Now that you have an agent running on your AKS cluster, you can start deploying Dagster code to it. You can follow the guide [here](acr-user-code) to deploy user code to your AKS cluster backed by Azure Container Registry (ACR).
