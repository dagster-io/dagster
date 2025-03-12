---
title: 'Alert policy types'
sidebar_position: 300
---

| Policy type | Triggers on | Notes | Availability | Example YAML |
|-------------|-------------|--------------|-------|----------|
| **Asset** | **Asset materializations** - Failure or success. If using a RetryPolicy, an alert will only be sent after all retries complete.<br /><br />**[Asset checks](/guides/test/asset-checks)** - Error, warn, passed, or failure to execute. By default, failed asset checks have a severity of `WARN`. | Asset alerts can be scoped to asset groups or specific asset keys. Asset check alerts are sent for any checks on those assets.<br /><br />If using **Dagster+ Pro**, asset alerts also allow you to send alerts to [asset owners](/guides/build/assets/metadata-and-tags/#owners).<br /><br />[External assets](/guides/build/assets/external-assets) do not trigger asset alerts. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments  | [TK](creating-alerts#using-the-cli) |
| **Run** | Triggers on job run success, failure, or time limit exceeded; may optionally include a set of configured tags. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments  | If an alert policy has no configured tags, all jobs will be eligible for that alert. Otherwise, only jobs that contain all the tags for a given alert policy are eligible for that alert.<br /><br />Each newly created organization starts with a long-running run alert policy, which sends an email to the email address used to create the organization when a job run exceeds 24 hours. | |
| **Code location** | Triggers when a code location fails to load due to an error. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments | | |
| **Automation** | Triggers when a tick failure occurs for schedules or sensors in the deployment. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments | Alerts are sent only when the schedule/sensor changes from **success** to **failure**, so subsequent failures won't trigger new alerts. | |
| **Insight metric** (Experimental) | Sends a notification when a [Dagster+ Insights](/dagster-plus/features/insights/) metric exceeds or falls below a specified threshold over a specified time window. This can be used to alert on:<ul><li>Dagster credit usage across a deployment or for a specific job</li><li>Performance regressions on asset or job runtime</li><li>Spend on external tools such as Snowflake or BigQuery credits</li></ul> | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments  | Alerts can be scoped to the sum of any metric across an entire deployment, or for a specific job, asset group, or asset key.<br /><br />Alerts are sent only when the threshold is first crossed, and will not be sent again until the value returns to expected levels. Insights data may become available up to 24 hours after run completion. | |
| **Agent downtime** | Triggers when a Hybrid agent hasn't heartbeated within the last five minutes. | [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments only. | | |
| **Credit budget** (Experimental) | Sends a notification when your organization has reached the monthly credit limit. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) deployments only | Each newly created organization starts with an alert policy of this type, directed at the email address used to create the organization. | |

## Asset alert

| Triggers on | Availability | Notes |
|-------------|-------------|--------|
| **Asset materializations** - Failure or success. If using a RetryPolicy, an alert will only be sent after all retries complete.<br /><br />**[Asset checks](/guides/test/asset-checks)** - Error, warn, passed, or failure to execute. By default, failed asset checks have a severity of `WARN`. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments | Asset alerts can be scoped to asset groups or specific asset keys. Asset check alerts are sent for any checks on those assets.<br /><br />If using **Dagster+ Pro**, asset alerts also allow you to send alerts to [asset owners](/guides/build/assets/metadata-and-tags/#owners).<br /><br />[External assets](/guides/build/assets/external-assets) do not trigger asset alerts.<br/><br/>If using a `RetryPolicy`, an alert will only be sent after all retries complete. |

### Alerting when an asset fails to materialize

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml" language="yaml" />
  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml" language="yaml" />
  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml" language="yaml" />
  </TabItem>
  <TabItem value='slack' label='Slack'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml" language="yaml" />
  </TabItem>
</Tabs>

### Alerting when an asset check fails

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/asset-check-failed-email.yaml" language="yaml" />
  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/asset-check-failed-microsoft_teams.yaml" language="yaml" />
  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/asset-check-failed-pagerduty.yaml" language="yaml" />
  </TabItem>
  <TabItem value='slack' label='Slack'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/asset-check-failed-slack.yaml" language="yaml" />
  </TabItem>
</Tabs>

## Run alert

| Triggers on | Availability | Notes |
|-------------|-------------|--------|
| Job run success, failure, or time limit exceeded; may optionally include a set of configured tags. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments  | Each newly created organization starts with a long-running run alert policy, which sends an email to the email address used to create the organization when a job run exceeds 24 hours.<br /><br />If an alert policy has no configured tags, all jobs will be eligible for that alert. Otherwise, only jobs that contain all the tags for a given alert policy are eligible for that alert. |

### Alerting when a run fails

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml" language="yaml" />
  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml" language="yaml" />
  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml" language="yaml" />
  </TabItem>
  <TabItem value='slack' label='Slack'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml" language="yaml" />
  </TabItem>
</Tabs>

### Alerting when a run is taking too long

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-email.yaml" language="yaml" />
  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-microsoft_teams.yaml" language="yaml" />
  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-pagerduty.yaml" language="yaml" />
  </TabItem>
  <TabItem value='slack' label='Slack'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-slack.yaml" language="yaml" />
  </TabItem>
</Tabs>

## Code location alert

| Triggers on | Availability |
|-------------|-------------|
| Triggers when a code location fails to load due to an error. | [Serverless](/dagster-plus/deployment/deployment-types/serverless/) and [Hybrid](/dagster-plus/deployment/deployment-types/hybrid/) deployments |

### Alerting when a code location fails to load

<Tabs groupId="notification_service">
  <TabItem value='email' label='Email'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/code-location-error-email.yaml" language="yaml" />
  </TabItem>
  <TabItem value='microsoft_teams' label='Microsoft Teams'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/code-location-error-microsoft_teams.yaml" language="yaml" />
  </TabItem>
  <TabItem value='pagerduty' label='PagerDuty'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/code-location-error-pagerduty.yaml" language="yaml" />
  </TabItem>
  <TabItem value='slack' label='Slack'>
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/code-location-error-slack.yaml" language="yaml" />
  </TabItem>
</Tabs>

## Automation alert

TK

## 

