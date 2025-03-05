---
title: Creating alert policies in Dagster+
sidebar_position: 200
---
{/* To update or regenerate the yaml code snippets in this doc, run `python ./examples/docs_beta_snippets/docs_beta_snippets/dagster-plus/deployment/alerts/generate_alerts_doc_code_snippets.py` */}

You can create alert policies in the Dagster+ UI or with the [`dagster-cloud` CLI](/dagster-plus/deployment/management/dagster-cloud-cli).

Alert policies are configured on a per-deployment basis. This means, for example, that asset alerts configured in a prod deployment are only applicable to assets in that deployment.

When you create an alert policy, you must select an alert policy type. For more information on the policy types, see "[Alert policy types](alert-policy-types)".

:::note

Before you create alert policies, you must [configure an alert notification service](configuring-an-alert-notification-service).

:::

## Alerting when a run fails

You can set up alerts to notify you when a run fails.

By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.
<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Run** from the menu and click **Continue**.
5. Choose run targets and events for your alert and click **Continue**.
6. Choose a notification channel for your Run alert and click **Continue**.
7. Review and save your Run alert and click **Save alert**.

If desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.

  </TabItem>
  <TabItem value='CLI' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when a run is taking too long to complete

You can set up alerts to notify you whenever a run takes more than some threshold amount of time.

By default, these alerts will target all runs in the deployment, but they can be scoped to runs with a specific tag.

<Tabs groupId="ui_or_cli">
  <TabItem value='ui' label='In the UI'>
    1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Run** from the menu and click **Continue**.
5. Choose run targets, select "Run exceeding a specified number of hours", enter the number of hours, and click **Continue**.
6. Choose a notification channel for your Run alert and click **Continue**.
7. Review and save your Run alert and click **Save alert**.

If desired, add **tags** in the format `{key}:{value}` to filter the runs that will be considered.

  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when an asset fails to materialize

You can set up alerts to notify you when an asset materialization attempt fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to a specific asset or group of assets.

:::note

If using a RetryPolicy, an alert will only be sent after all retries complete.

:::

<Tabs groupId="ui_or_cli">
<TabItem value='ui' label='In the UI'>
1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Asset** from the menu and click **Continue**.
5. Choose asset targets and events and click **Continue**.
6. Choose a notification channel for your asset alert and click **Continue**.
7. Review and save your asset alert and click **Save alert**.


  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when an asset check fails

You can set up alerts to notify you when an asset check on an asset fails.

By default, these alerts will target all assets in the deployment, but they can be scoped to checks on a specific asset or group of assets.
<Tabs groupId="ui_or_cli">
<TabItem value='ui' label='In the UI'>
1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Asset** from the menu and click **Continue**.
5. Choose asset targets, select the relevant asset check events, and click **Continue**.
6. Choose a notification channel for your asset alert and click **Continue**.
7. Review and save your asset alert and click **Save alert**.

  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when a schedule or sensor tick fails

You can set up alerts to fire when any schedule or sensor tick across your entire deployment fails.

Alerts are sent only when a schedule/sensor transitions from **success** to **failure**, so only the initial failure will trigger the alert.
<Tabs groupId="ui_or_cli">
<TabItem value='ui' label='In the UI'>
1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Automation** from the menu and click **Continue**.
5. Select the tick types to be alerted on. Choose if you only want to be alerted after `n` consecutive failures and click **Continue**.
6. Choose a notification channel for your automation alert and click **Continue**.
7. Review and save your automation alert and click **Save alert**.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when a code location fails to load

You can set up alerts to fire when any code location fails to load due to an error.
<Tabs groupId="ui_or_cli">
<TabItem value='ui' label='In the UI'>
1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Code Location** from the menu and click **Continue**.
5. Select your target and click **Continue**.
6. Choose a notification channel for your code location alert and click **Continue**.
7. Review and save your code location alert and click **Save alert**.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>

## Alerting when a Hybrid agent becomes unavailable

:::note

Alerting when a Hybrid agent becomes unavailable is only available for [Hybrid deployments](/dagster-plus/deployment/deployment-types/hybrid/).

:::

You can set up alerts to fire if your Hybrid agent hasn't sent a heartbeat in the last 5 minutes.
<Tabs groupId="ui_or_cli">
<TabItem value='ui' label='In the UI'>
1. In the Dagster UI, click **Deployment**.
2. Click the **Alert policies** tab.
3. Click **Create alert policy**.
4. Select **Code Location** from the menu and click **Continue**.
5. Select your target and click **Continue**.
6. Choose a notification channel for your code location alert and click **Continue**.
7. Review and save your code location alert and click **Save alert**.
  </TabItem>
  <TabItem value='cli' label='Using the CLI'>
    Execute the following command to sync the configured alert policy to your Dagster+ deployment.

  ```bash
  dagster-cloud deployment alert-policies sync -a /path/to/alert_policies.yaml
  ```
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

  </TabItem>
</Tabs>
