# Summarize failing run in Dagster

Find the errors associated with the run by using the `dg api log get` command for the provided run ID:

    dg api log get $1 --json | jq '.logs[] | select(.level == "ERROR")'

Then, summarize the issue and identify the root cause of the problem.

If there are no errors when filtering with `jq` `select(.level == "ERROR")` then retrieve the full logs:

    dg api log get $1 --json

And provide a summary of the run
