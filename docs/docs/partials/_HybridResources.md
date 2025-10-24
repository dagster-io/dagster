- **Agent container** - Start at 0.25 vCPU core and 1 GB RAM, then scale with [concurrent runs](/guides/operate/managing-concurrency) and the number and size of [code locations](/deployment/code-locations/dagster-plus-code-locations).
- **Code server container** - Budget for imports, plus the definition graph, and any heavy initialization. We recommend starting with 0.25 vCPU cores and 1GB RAM.
- **Runs:** 4 vCPU cores, 8-16 GB of RAM depending on the workload

For compute-heavy jobs, increase memory and/or CPU where the run workers are (i.e. Kubernetes pods or ECS tasks), not just the code server.
