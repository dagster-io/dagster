---
title: Creating alerts in Dagster+
sidebar_position: 200
---

You can create alerts in the Dagster+ UI or using the [`dagster-cloud` CLI](/dagster-plus/deployment/management/dagster-cloud-cli).

{/** TODO link to dagster-cloud CLI tool doc **/}

:::note
Before you create alerts, you must [configure an alert notification service](configuring-an-alert-notification-service).
:::

## Alerting when a run fails

You can set up alerts to notify you when a run fails.

By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Run alert** from the dropdown.

5. Select **Job failure**.

If desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.

  </TabItem>
  <TabItem value='CLI' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when a run is taking too long to complete

You can set up alerts to notify you whenever a run takes more than some threshold amount of time.

        By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Run alert** from the dropdown.

5. Select **Job running over** and how many hours to alert after.

If desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.

  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/job-running-over-one-hour-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/job-running-over-one-hour-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/job-running-over-one-hour-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/job-running-over-one-hour-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when an asset fails to materialize

You can set up alerts to notify you when an asset materialization attempt fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to a specific asset or group of assets.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Asset alert** from the dropdown.

5. Select **Failure** under the **Materializations** heading.

If desired, select a **target** from the dropdown menu to scope this alert to a specific asset or group.

  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when an asset check fails

You can set up alerts to notify you when an asset check on an asset fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to checks on a specific asset or group of assets.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Asset alert** from the dropdown.

5. Select **Failed (ERROR)** under the **Asset Checks** heading.

If desired, select a **target** from the dropdown menu to scope this alert to a specific asset or group.

  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/asset-check-failed-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/asset-check-failed-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/asset-check-failed-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/asset-check-failed-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when a schedule or sensor tick fails

You can set up alerts to fire when any schedule or sensor tick across your entire deployment fails.

Alerts are sent only when a schedule/sensor transitions from **success** to **failure**, so only the initial failure will trigger the alert.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Schedule/Sensor alert** from the dropdown.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/schedule-sensor-failure-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when a code location fails to load

You can set up alerts to fire when any code location fails to load due to an error.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Code location error alert** from the dropdown.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>

## Alerting when a Hybrid agent becomes unavailable

:::note
This is only available for [Hybrid](/todo) deployments.
:::

You can set up alerts to fire if your Hybrid agent hasn't sent a heartbeat in the last 5 minutes.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alerts** tab.
3. Click **Add alert policy**.
4. Select **Code location error alert** from the dropdown.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

```bash
dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
```

{' '}
<Tabs groupId="notification_service">
<TabItem value="email" label="Email">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-email.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="microsoft_teams" label="Microsoft Teams">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-microsoft_teams.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="pagerduty" label="PagerDuty">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-pagerduty.yaml"
      language="yaml"
    />
</TabItem>
<TabItem value="slack" label="Slack">
<CodeExample
      filePath="dagster-plus/deployment/alerts/code-location-error-slack.yaml"
      language="yaml"
    />
</TabItem>
</Tabs>

  </TabItem>
</Tabs>
