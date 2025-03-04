---
title: "Interactive debugging with pdb"
description: 'Learn how to use pdb for interactive debugging'
sidebar_position: 10
---

Sometimes you may want to debug an asset while it is executing. To simplify this process, Dagster supports interactive debugging with [pdb](https://docs.python.org/3/library/pdb.html) through the <PyObject section="execution" module="dagster" object="AssetExecutionContext" /> of an asset. pdb is useful when you need to step through code line-by-line to identify and fix bugs by inspecting variables and program flow in real time.

## Setting pdb

Add `context.pdb.set_trace()` to the asset code where you want to enter the debugger.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/monitor-alert/debugging/pdb.py" language="python" />

Next you can launch the asset locally from your terminal with `dagster dev`. When the asset is materialized, the execution in the Dagster will wait on the asset where pdb has been set.

![pdb Asset Running](/images/guides/monitor/debugging/pdb-asset-running.png)

In the terminal where running `dagster dev`, there will now be a pdb debugger.

```bash
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52536 - RUN_START - Started execution of run for "__ASSET_JOB".
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52536 - ENGINE_EVENT - Executing steps using multiprocess executor: parent process (pid: 52536)
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52536 - pdb_asset - STEP_WORKER_STARTING - Launching subprocess for "pdb_asset".
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52540 - pdb_asset - STEP_WORKER_STARTED - Executing step "pdb_asset" in subprocess.
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52540 - pdb_asset - RESOURCE_INIT_STARTED - Starting initialization of resources [io_manager].
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52540 - pdb_asset - RESOURCE_INIT_SUCCESS - Finished initialization of resources [io_manager].
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52540 - LOGS_CAPTURED - Started capturing logs in process (pid: 52540).
2025-03-03 15:24:55 -0600 - dagster - DEBUG - __ASSET_JOB - 202cd42f-ecf3-4504-838c-e41f58dbdf78 - 52540 - pdb_asset - STEP_START - Started execution of step "pdb_asset".
--Return--
> /Users/dennis/code/dagster-quickstart/debugging.py(11)pdb_asset()
-> x += 5
(Pdb)
```

## Accessing variables

The pdb debugger will be at the point in the asset where `context.pdb.set_trace()` was set and give you access to any of the variables within the asset at that point in the asset code.

```bash
(Pdb) x
10
```

You can keep navigate through the asset code using any [pdb commands](https://realpython.com/python-debugging-pdb/#essential-pdb-commands) and access variables at different points to see how values change over time. 

```bash
> /Users/dennis/code/dagster-quickstart/debugging.py(11)pdb_asset()
-> x += 5
(Pdb) x
10
(Pdb) next
> /Users/dennis/code/dagster-quickstart/debugging.py(12)pdb_asset()
-> x += 20
(Pdb) x
15
(Pdb) next
> /Users/dennis/code/dagster-quickstart/debugging.py(13)pdb_asset()
-> return x
(Pdb) x
35
(Pdb)
```

While these pdb commands occur in the terminal, they will also be recorded in `stdout` of the Dagster asset execution.

![pdb stdout](/images/guides/monitor/debugging/stdout.png)

## Continuing execution

The asset will remain in the "materializing" state until all the statements of the asset have been navigated through using `next` or `continue` is executed within pdb. The asset will then finish materializing and close pdb in the terminal.

![pdb Asset Success](/images/guides/monitor/debugging/pdb-asset-success.png)
