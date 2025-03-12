---
title: Creating alert policies in Dagster+
sidebar_position: 200
---
{/* To update or regenerate the yaml code snippets in this doc, run `python ./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/generate_alerts_doc_code_snippets.py` */}

You can create alert policies in the Dagster+ UI or with the [`dagster-cloud` CLI](/dagster-plus/deployment/management/dagster-cloud-cli).

Alert policies are configured on a per-deployment basis. This means, for example, that asset alerts configured in a prod deployment are only applicable to assets in that deployment.


:::note

Before you can create alert policies, you will need to [configure an alert notification service](configuring-an-alert-notification-service).

:::

## In the UI

1. In the Dagster UI, click **Deployment**.
2. In the left sidebar, click **Alert policies**.
3. Click **Create alert policy**.
4. Choose the [policy type](alert-policy-types) from the menu and click **Continue**.
5. Choose targets and events (if applicable) for your alert and click **Continue**.
6. Choose a notification channel for your alert and click **Continue**.
7. Review and save your alert and click **Save alert**.

## Using the CLI

Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

For example configurations, see below.

### Asset

### Run

### Code location

### Automation

#### Alerting when a schedule or sensor tick fails

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

### Insight metric

### Agent downtime

### Credit budget

## Alerting when a code location fails to load

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

## Alerting when a Hybrid agent becomes unavailable

:::note

Alerting when a Hybrid agent becomes unavailable is only available for [Hybrid deployments](/dagster-plus/deployment/deployment-types/hybrid/).

:::

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