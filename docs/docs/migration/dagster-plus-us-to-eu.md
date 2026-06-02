---
title: Dagster+ US to Dagster+ EU
description: Migrate your Dagster+ organization from the US region to the EU region for data residency compliance.
sidebar_label: Dagster+ US to EU
sidebar_position: 50
tags: [dagster-plus-feature]
---

With [Dagster+ EU](/deployment/dagster-plus/dagster-plus-eu), your control plane, metadata, and operational data reside in European data centers (`eu-north-1`). This guide covers how to migrate from the US to the EU control plane.

Because US and EU are separate Dagster+ control planes, migration requires creating a new organization in the EU region and re-configuring your agents, CI/CD, and SSO configuration. Your actual pipeline code does not change — the migration is entirely about infrastructure and configuration.

:::warning

Dagster+ does not support automatic migration of metadata between regions. Run history, schedules, sensors, and other operational state do not transfer. Asset materialization metadata can be migrated manually — see [Step 7](#step-7-migrate-asset-metadata-optional). Plan your cutover accordingly.

:::

## Prerequisites

- [**Organization Admin**](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) permissions in your existing US Dagster+ organization
- Access to your CI/CD configuration (GitHub Actions, GitLab CI, etc.)
- Access to your agent infrastructure (Kubernetes, Amazon Elastic Container Service (ECS), Docker, etc.) if using Hybrid

## Step 1: Create a new Dagster+ EU organization

[Create a new Dagster+ organization in the EU region](https://eu.dagster.cloud/signup). Your EU organization URL will be:

```
https://<organization_name>.eu.dagster.cloud
```

After signing up, choose the same deployment type (Serverless or Hybrid) that you use in the US region.

## Step 2: Set up users and authentication

Re-create your user and team configuration in the EU organization:

1. **Invite users** — Add team members to the EU organization through **Organization Settings > Users**.

2. **Configure single sign-on (SSO)** — If you use SSO, set up a new SSO integration pointing to the EU region. In your identity provider (Okta, Microsoft Entra ID, Google Workspace, etc.), update the following:

   - **Sign-on URL / ACS URL** — Use `https://<organization_name>.eu.dagster.cloud` instead of `https://<organization_name>.dagster.cloud`
   - **Audience URI / Entity ID** — Update to the EU organization URL

   For provider-specific instructions, see the [SSO documentation](/deployment/dagster-plus/authentication-and-access-control/sso).

3. **Configure System for Cross-domain Identity Management (SCIM)** (if applicable) — If you use [SCIM provisioning](/deployment/dagster-plus/authentication-and-access-control/scim), update the SCIM base URL and generate a new SCIM token in the EU organization.

## Step 3: Configure your agent (Hybrid only)

If you're using a Hybrid deployment, you need to point your agent to the EU control plane.

### Generate a new agent token

Generate a new agent token in your EU organization by navigating to **Organization Settings > Tokens** and clicking **+ Create agent token**. For details, see [Managing agent tokens](/deployment/dagster-plus/management/tokens/agent-tokens).

### Update agent configuration

Update your agent configuration to use the new EU agent token. The only change needed is replacing the agent token — the agent automatically connects to the correct region using the token. Follow the setup instructions for your agent type:

- [Kubernetes](/deployment/dagster-plus/hybrid/kubernetes/setup)
- [Amazon ECS](/deployment/dagster-plus/hybrid/amazon-ecs)
- [Docker](/deployment/dagster-plus/hybrid/docker/setup)
- [Local](/deployment/dagster-plus/hybrid/local)

### Update network allowlists

If your infrastructure uses IP or URL allowlists, update them with the EU region values listed in [Dagster+ IP addresses](/deployment/dagster-plus/management/dagster-ips).

## Step 4: Update CI/CD configuration

Update the CI/CD secrets and configuration in your repository to point to the EU organization:

1. **`DAGSTER_CLOUD_URL`** — Change from `https://<org>.dagster.cloud` to `https://<org>.eu.dagster.cloud`
2. **`DAGSTER_CLOUD_API_TOKEN`** — Generate a new API token in the EU organization and update the secret

For provider-specific instructions, see [Configuring CI/CD in Dagster+](/deployment/dagster-plus/deploying-code/configuring-ci-cd).

## Step 5: Deploy your code

Deploy your code to the EU organization:

- **Serverless** — Push to your repository's main branch to trigger a deployment via CI/CD.
- **Hybrid** — Confirm your agent is running and connected in the EU organization by navigating to **Deployment > Agents**. The agent should display with a `RUNNING` status.

Your pipeline code does not need to change. The same `build.yaml` and code location configuration will work in both regions.

## Step 6: Migrate deployment settings

Migrate your deployment-level configuration from the US organization to the EU organization using the `dg` CLI. You will need to [log in](/api/clis/dg-cli/configuring-dagster-plus) to each organization with `dg plus login` before running these commands.

### Environment variables and secrets

Migrate environment variables from the US organization to the EU organization. Choose the approach that best fits your needs:

<Tabs>
<TabItem value="manual" label="Manual">

Log in to your US organization and list your environment variables:

```bash
dg plus login
dg api secret list
```

Then log in to the EU organization and re-create each variable:

```bash
dg plus login
dg plus create env ENV_NAME ENV_VALUE -y
```

Repeat `dg plus create env` for each environment variable.

</TabItem>
<TabItem value="scripted" label="Scripted">

The following script exports all environment variables from the US organization and re-creates them in the EU organization.

First, log in to the US organization, export the variable list, and retrieve each value:

```bash
dg plus login
dg api secret list --json > env_vars.json

for name in $(python -c "import sys,json; [print(s['name']) for s in json.load(open('env_vars.json'))['items']]"); do
  value=$(dg api secret get "$name" --show-value --json | python -c "import sys,json; print(json.load(sys.stdin)['value'])")
  echo "$name=$value" >> env_values.txt
done
```

Then, log in to the EU organization and create all variables:

```bash
dg plus login
while IFS='=' read -r name value; do
  dg plus create env "$name" "$value" -y
done < env_values.txt
```

:::warning

The `env_values.txt` file contains secret values in plain text. Delete it after migration is complete.

:::

</TabItem>
</Tabs>

For details, see the [environment variables documentation](/deployment/dagster-plus/management/environment-variables).

### Alert policies

Export alert policies from the US deployment as YAML, then sync them to the EU deployment:

```bash
# Log in to US organization and export
dg plus login
dg api alert-policy list > alert_policies.yaml

# Log in to EU organization and sync
dg plus login
dg api alert-policy sync alert_policies.yaml
```

For details, see the [alert policies documentation](/guides/observe/alerts/creating-alerts) and [YAML reference](/guides/observe/alerts/yaml-reference).

### Deployment settings

Export deployment settings from the US organization and apply them to the EU organization:

```bash
# Log in to US organization and export
dg plus login
dg api deployment settings get > deployment_settings.yaml

# Log in to EU organization and apply
dg plus login
dg api deployment settings set deployment_settings.yaml
```

### Schedules and sensors

[Schedules and sensors](/guides/automate) are defined in code and will be deployed automatically, but verify their toggle state (enabled/disabled) matches your expectations.

## Step 7: Migrate asset metadata (optional)

After deploying your code to the EU organization, you can optionally migrate historical asset materialization metadata from the US organization. Without this step, the EU organization starts without metadata, and metadata accumulates from new materializations going forward.

To migrate metadata, use the Dagster+ [REST API to report asset materializations](/api/rest-api) against the EU organization. The [`oss-metadata-to-plus` example](https://github.com/dagster-io/dagster/tree/master/examples/oss-metadata-to-plus) demonstrates this pattern: it reads materialization records from a source instance and replays them to a target organization via the `report_asset_materialization` endpoint.

To adapt this for a US-to-EU migration, point the REST API calls at your EU organization URL:

```
https://<organization_name>.eu.dagster.cloud/<deployment_name>/report_asset_materialization/
```

Authenticate with an [agent token](/deployment/dagster-plus/management/tokens/agent-tokens) from the EU organization and provide the `Dagster-Cloud-Api-Token` header.

:::note

This approach migrates asset materialization metadata (timestamps, partition status, user-defined metadata). It does not migrate run history, schedules, sensors, or other operational state.

:::

## Step 8: Configure Compute Log Storage in EU (optional)

Configure [compute log storage](/deployment/dagster-plus/management/managing-compute-logs-and-error-messages) in EU infrastructure.
