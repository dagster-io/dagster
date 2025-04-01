---
title: 'Example alert policy configuration'
sidebar_position: 400
---

{/* To update or regenerate the yaml code snippets in this doc, run `python ./examples/docs_snippets/docs_snippets/dagster-plus/deployment/alerts/generate_alerts_config_code_snippets.py` */}

If you prefer to manage your alerts through configuration files instead of the UI, you can create a YAML file using the following snippets and adjust as needed. To sync the file to your Dagster+ deployment, run:

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

## Asset alert

### Alerting when an asset fails to materialize

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-materialization-failure-alert-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-materialization-failure-alert-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-materialization-failure-alert-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-materialization-failure-alert-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

### Alerting when an asset check fails

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-check-failed-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-check-failed-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-check-failed-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/asset-check-failed-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

## Run alert

### Alerting when a run fails

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/run-alert-failure-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/run-alert-failure-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/run-alert-failure-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/run-alert-failure-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

### Alerting when a run is taking too long to complete

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/job-running-over-one-hour-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

## Code location alert

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/code-location-error-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/code-location-error-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/code-location-error-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/code-location-error-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

## Automation alert

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

## Agent unavailable alert

:::note

Alerting when a Hybrid agent becomes unavailable is only available for [Hybrid deployments](/dagster-plus/deployment/deployment-types/hybrid/).

:::

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/agent-unavailable-alert-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/agent-unavailable-alert-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/agent-unavailable-alert-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/agent-unavailable-alert-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>

## Credit budget alert

:::note

The example configuration below can be used in both Serverless and Hybrid deployments.

:::

<Tabs groupId="notification_service">
  <TabItem value="email" label="Email">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/credit-budget-alert-email.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="microsoft_teams" label="Microsoft Teams">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/credit-budget-alert-microsoft_teams.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="pagerduty" label="PagerDuty">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/credit-budget-alert-pagerduty.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="slack" label="Slack">
    <CodeExample
      path="docs_snippets/docs_snippets/dagster-plus/deployment/alerts/credit-budget-alert-slack.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>
