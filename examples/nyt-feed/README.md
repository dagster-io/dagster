## New York Times feed example

A job that pulls down metadata about New York Times articles, writes them to a CSV, and reports them in Slack.

### Loading the example in Dagit

    dagit -w workspace.yaml

### Features demonstrated

- Conditional branching.
- Custom `IOManager`.
- Reusing an op twice in the same job.
