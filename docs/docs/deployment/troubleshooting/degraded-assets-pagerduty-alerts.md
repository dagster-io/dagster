---
title: PagerDuty alerts are less than the number of degraded assets in Dagster+
sidebar_position: 140
description: Explain why PagerDuty alert counts don't match the number of degraded assets, and how to configure policies for better alert distribution.
---

## Problem description

Users may notice that they receive fewer PagerDuty alerts than the actual number of degraded assets shown in their Dagster+ deployment.

## Symptoms

- Multiple assets showing as degraded in Dagster+ (e.g., 27 assets).
- Fewer PagerDuty alerts received than expected (e.g., only 10 alerts for 27 degraded assets).
- Alert policy appears to be configured correctly to cover all assets.

## Root cause

This discrepancy occurs when multiple assets degrade simultaneously but the alerting system doesn't send individual notifications for each asset.

Asset health alerts only notify once when the health status changes, not for every degraded asset. When multiple assets degrade simultaneously, the alerting system may batch or deduplicate notifications. Additionally, PagerDuty may have rate limits or batching behavior that prevents all alerts from being delivered when many are triggered at once.

## Solution

Verify your alert policy scope covers all intended assets and check PagerDuty integration configuration for rate limits.

### Step-by-step resolution

1. Review your alert policy configuration to ensure it covers all assets you want to monitor.
2. Check if your alert policy has filters (asset groups, tags, or owners) that might exclude some assets.
3. Verify your PagerDuty integration is correctly configured and not hitting event limits.

### Alternative solutions

Create separate alert policies for different asset groups to get more granular control over notifications and reduce batching effects.

## Prevention

Set up multiple alert policies grouped by asset categories or criticality levels to ensure better alert distribution and avoid overwhelming notification services with simultaneous alerts.

## Related documentation

- [Creating alert policies](/guides/observe/alerts/creating-alerts)
- [Configuring alert notification services](/guides/observe/alerts/configuring-an-alert-notification-service)
