---
title: Dagster+ Hybrid performance optimization and troubleshooting
description: Configure your agent and code server container settings for optimal performance of your Dagster+ deployment.
sidebar_position: 300
---

To avoid running into performance issues, we recommend tailoring your agent and code server settings for your deployment using the recommendations in the [performance optimization](#performance-optimization) section.

If you run into issues as you scale your deployment (especially as asset counts increase), you can use the [troubleshooting suggestions](#troubleshooting) to diagnose and fix them.

## Performance optimization

* **Agent** - Start at 0.25 vCPU core and 1 GB RAM, then scale with [concurrent runs](/guides/operate/managing-concurrency) and the number and size of [code locations](/deployment/code-locations/dagster-plus-code-locations).
* **Code server** - Budget for imports, plus the definition graph, and any heavy initialization. We recommend starting with 0.25 vCPU cores and 1GB RAM.

For compute-heavy jobs, increase memory and/or CPU where the run workers are (i.e. Kubernetes pods or ECS tasks), not just the code server.

## Troubleshooting

### General advice

* Look for `exit code 137` / `OOMKilled` in the agent or code server container logs -- this is the strongest signal that the issue is insufficient memory.
* Correlate heartbeat timeouts (agent or code server) with CPU spikes or container restarts.
* Distinguish issues where the run never starts (agent can’t schedule workers) from those where the run starts, then dies (worker or code server out of memory).
* If errors disappear when you lower concurrency, this is a signal that you were hitting CPU/RAM saturation with the previous concurrency settings.

### Agent troubleshooting

| Symptom | Solution |
|---------|----------|
| "Agent heartbeat timed out", "No healthy agents available", or agent disconnected messages. | Correlate heartbeat timeouts with CPU spikes or container restarts; increase CPU in agent container as needed. |
| Runs sitting in "Queued" or "Starting" for a long time with no worker ever spawned | |
| "Failed to start run worker", "Run worker never started", or repeated retries to launch tasks. | |
| Repeated agent restarts; logs show `OOMKilled`, `exit code 137`, or generic `Killed` | Increase memory in agent container. |
| `gRPC DeadlineExceeded` or `UNAVAILABLE` between Dagster+ and the agent, especially under load. This usually indicates too little network egress to keep up. | Update network settings. |
| Backpressure symptoms, such as log streaming interruptions, sporadic "unable to report event"-style messages | |

### Code server troubleshooting

| Symptom | Solution |
|---------|----------|
| "Failed to load code location" error with `MemoryError`, `OutOfMemory`, or plain `Killed / exit 137`. | Increase memory in code server container. |
| Kubernetes pod or ECS task shows `OOMKilled`, `CrashLoopBackOff`, or ECS `OutOfMemoryError`. | Increase memory in code server container. |
| gRPC server crashed, `UserCodeUnreachable` errors, or `Can’t connect to user code server` errors (often after long import times). | |
| Load or health check timeouts when you click into the location or expand assets in the UI. | |
| During runs:<br /><ul><li>`Worker exited with SIGKILL (OOM)` error</li><li>Python `MemoryError` from libraries (pandas, numpy, PyTorch, etc.)</li><li>gRPC DeadlineExceeded mid-run when the user code process stalls under GC or thrash.</li></ul> | Increase memory in code server container. |
| Sensors/schedules that query a large graph timing out when the code server has limited CPU. | Increase CPU in code server container. |