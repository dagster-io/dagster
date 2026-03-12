---
title: Dagster+ Hybrid performance optimization and troubleshooting
description: Configure your agent and code server container settings for optimal performance of your Dagster+ deployment.
sidebar_position: 100
---

import HybridResources from '@site/docs/partials/\_HybridResources.md';

To ensure the best performance of your Dagster+ deployment, we recommend following the guidance in the [performance optimization](#performance-optimization) section of this doc to tune your [agent](/deployment/dagster-plus/hybrid/architecture#the-agent) and [code server](/deployment/dagster-plus/hybrid/architecture#code-server) container settings to meet your organization's needs.

If you run into issues as you scale your deployment (especially as asset counts increase), you can use the [troubleshooting guidance](#troubleshooting) to diagnose and fix them.

## Performance optimization

<HybridResources />

## Troubleshooting

### General guidance

- Look for `exit code 137` / `OOMKilled` in the agent or code server container logs -- this is the strongest signal that the issue is insufficient memory.
- Correlate heartbeat timeouts (agent or code server) with CPU spikes or container restarts.
- Distinguish issues where the run never starts (agent can’t schedule workers) from those where the run starts, then dies (worker or code server out of memory).
- If errors disappear when you lower concurrency, this is a signal that you were hitting CPU/RAM saturation with the previous concurrency settings.

### Agent server troubleshooting

| Symptom                                                                                                                                                      | Solution                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| "Agent heartbeat timed out", "No healthy agents available", or agent disconnected messages.                                                                  | Correlate heartbeat timeouts with CPU spikes or container restarts; increase CPU in agent container as needed. |
| Runs sitting in "Queued" or "Starting" for a long time with no worker ever spawned                                                                           |                                                                                                                |
| "Failed to start run worker", "Run worker never started", or repeated retries to launch tasks.                                                               |                                                                                                                |
| Repeated agent restarts; logs show `OOMKilled`, `exit code 137`, or generic `Killed`                                                                         | Increase memory in agent container.                                                                            |
| `gRPC DeadlineExceeded` or `UNAVAILABLE` between Dagster+ and the agent, especially under load. This usually indicates too little network egress to keep up. | Update network settings.                                                                                       |
| Backpressure symptoms, such as log streaming interruptions, sporadic "unable to report event"-style messages                                                 |                                                                                                                |

### Agent connectivity issues

Kubernetes-based Dagster+ agents may experience intermittent request timeouts when communicating with Dagster Cloud servers. Common error messages include:

- `Read timed out. (read timeout=60)` on HTTPS connections
- Connection reset errors during agent-to-API communication
- `CrashLoopBackOff` errors caused by repeated connection failures

#### Root causes

These timeouts typically occur in hybrid Kubernetes deployments where:

- Network traffic passes through NAT gateways or proxies with strict idle connection timeouts
- Connections are dropped between the agent and Dagster+ API endpoints due to infrastructure-level timeouts
- Port or IP exhaustion issues exist, particularly on cloud provider NAT services (for example, GCP CloudNAT)

#### Solutions

**Upgrade Dagster version**: Update to Dagster 1.5.9 or later, which adds automatic retry logic to agent API calls for improved resilience against transient network failures.

**Enable TCP keepalive (Kubernetes)**: For Kubernetes agents using Helm chart version 1.7.3 or later, configure TCP keepalive settings to proactively detect and recover from broken connections. Add the following to your Helm values:

```yaml
dagsterCloud:
  socketOptions:
    - ['SOL_SOCKET', 'SO_KEEPALIVE', 1]
    - ['IPPROTO_TCP', 'TCP_KEEPIDLE', 11]
    - ['IPPROTO_TCP', 'TCP_KEEPINTVL', 7]
    - ['IPPROTO_TCP', 'TCP_KEEPCNT', 5]
```

These socket options configure the following behavior:

| Option          | Value | Description                                         |
| --------------- | ----- | --------------------------------------------------- |
| `SO_KEEPALIVE`  | 1     | Enables TCP keepalive probing                       |
| `TCP_KEEPIDLE`  | 11    | Seconds of idle time before sending the first probe |
| `TCP_KEEPINTVL` | 7     | Seconds between subsequent probes                   |
| `TCP_KEEPCNT`   | 5     | Number of failed probes before closing connection   |

:::note

These settings are relatively aggressive and will increase network traffic. Adjust the values based on your infrastructure's NAT gateway or proxy timeout settings. A common approach is to set `TCP_KEEPIDLE` to a value lower than your NAT gateway's idle timeout.

:::

### Code server troubleshooting

| Symptom                                                                                                                                                                                                                                             | Solution                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| "Failed to load code location" error with `MemoryError`, `OutOfMemory`, or plain `Killed / exit 137`.                                                                                                                                               | Increase memory in code server container. |
| Kubernetes pod or ECS task shows `OOMKilled`, `CrashLoopBackOff`, or ECS `OutOfMemoryError`.                                                                                                                                                        | Increase memory in code server container. |
| gRPC server crashed, `UserCodeUnreachable` errors, or `Can’t connect to user code server` errors (often after long import times).                                                                                                                   |                                           |
| Load or health check timeouts when you click into the location or expand assets in the UI.                                                                                                                                                          |                                           |
| During runs:<br /><ul><li>`Worker exited with SIGKILL (OOM)` error</li><li>Python `MemoryError` from libraries (pandas, numpy, PyTorch, etc.)</li><li>gRPC DeadlineExceeded mid-run when the user code process stalls under GC or thrash.</li></ul> | Increase memory in code server container. |
| Sensors/schedules that query a large graph timing out when the code server has limited CPU.                                                                                                                                                         | Increase CPU in code server container.    |
