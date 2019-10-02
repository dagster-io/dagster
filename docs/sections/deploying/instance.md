# Instance Configuration

A Dagster instance is composed of:

- Event Log Storage: Stores the record of structured events produced during runs. Ideally implementations allow for monitoring the event log in some capacity to enable real time monitoring via Dagit.

- Run Storage: Used to keep track of runs over time and query select subsets of them. Separate from the event log store to allow for efficient queries of run history.

- Compute Log Manager: Makes available copies of stdout and stderr on a per execution step basis for debugging. This includes a real time subscription component as well as optional hooks for storage.

- Local Artifact Storage: This ensures that a singular directory is used for all the file system artifacts produced by Dagster. This is useful for both sharing intermediates across multiple executions or simply to provide a single point of audit.

Tools like the Dagster CLI or Dagit use the following behavior to select the current instance:

1. Use the explicit settings in `$DAGSTER_HOME/dagster.yaml` if they exist
2. Create a local instance rooted at `$DAGSTER_HOME` if it is set
3. Create a local instance in the fallback directory if provided (used by dagit to maintain history between restarts)
4. Use an ephemeral instance, which will hold information in memory and use a TemporaryDirectory for local artifacts
   which is cleaned up on exit. This is useful for tests and is the default for direct python api invocations such
   as `execute_pipeline`.
