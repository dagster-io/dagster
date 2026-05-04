---
title: 'Debugging Dagster with VS Code (debugpy)'
description: Attach the VS Code debugger to a running Dagster process via debugpy.
sidebar_position: 20
---

`pdb` (covered in the [previous guide](/guides/log-debug/debugging/debugging-pdb)) is great when you want to drop into a single asset on demand. When you want a full IDE debugging experience — breakpoints, watch expressions, and step-through debugging across the entire Dagster process — VS Code's [`debugpy`](https://github.com/microsoft/debugpy) is the way to go.

The most reliable way to wire `debugpy` into Dagster is **attach mode**: run Dagster normally and connect the debugger to the already-running process. Trying to launch Dagster *through* `debugpy` (`request: "launch"` with `module: "dagster"`) ends up re-execing the CLI through `debugpy`'s launcher, which can break the gRPC code-server subprocess Dagster spawns — you'll see errors like `No module named dagster` from the child process.

## Step 1: Add a `debugpy` listener to your project

In your project's definitions module (the one referenced by `tool.dg.project.code_location_target_module` or its `Definitions(...)` equivalent), gate a `debugpy.listen()` call behind an environment variable so it only runs when you ask for it:

```python title="src/<my_project>/definitions.py"
"""Dagster definitions entry point for this project."""

import os
from pathlib import Path

from dagster import Definitions, definitions, load_from_defs_folder

# Enable remote debugging when DAGSTER_DEBUG is set.
if os.environ.get("DAGSTER_DEBUG"):
    try:
        import debugpy
    except ImportError:
        print("debugpy not installed — install it with your dev tooling.")
        debugpy = None  # type: ignore[assignment]

    if debugpy is not None:
        try:
            debugpy.listen(("localhost", 5678))
            print("debugpy listening on port 5678 — attach your IDE debugger")
        except RuntimeError:
            # Subprocess: pause briefly so debugpy can sync breakpoints from VS Code
            debugpy.trace_this_thread(True)
            import time

            time.sleep(0.5)


@definitions
def defs() -> Definitions:
    """Load all Dagster definitions from the defs/ folder."""
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
```

The `RuntimeError` branch handles Dagster's multiprocess executor. When Dagster spawns a code-server or step subprocess it re-imports your definitions module; the second `listen()` call raises because the port is already in use, so we fall through to `trace_this_thread(True)` and a small sleep that lets VS Code sync breakpoints into the child process before it starts executing user code.

## Step 2: Add a VS Code launch configuration

```json title=".vscode/launch.json"
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Dagster: Attach",
      "type": "debugpy",
      "request": "attach",
      "connect": {"host": "localhost", "port": 5678},
      "justMyCode": false
    }
  ]
}
```

`justMyCode: false` is optional — set it if you want to step into Dagster's own code or third-party libraries.

## Step 3: Run Dagster with debugging enabled

```sh
DAGSTER_DEBUG=1 dg dev
```

When you see `debugpy listening on port 5678` in the terminal, switch to VS Code and run the **Dagster: Attach** configuration. Set breakpoints in your asset, sensor, or schedule code and trigger a materialisation as normal — execution will pause at your breakpoints.

The same pattern works with `dagster dev`, `dagster job execute`, and any custom scripts that import your project's definitions module.

## Why not `request: "launch"`?

`request: "launch"` with `module: "dagster"` makes VS Code re-execute the Dagster CLI through `debugpy`'s launcher. Dagster then spawns a gRPC code-server subprocess to load your code, and that child process inherits an environment from the launcher that doesn't always have `dagster` resolvable on `sys.path`. Symptoms include:

```
DagsterUserCodeProcessError: gRPC server exited with return code 0 while starting up
…
ModuleNotFoundError: No module named 'dagster'
```

Attach mode sidesteps this entirely — Dagster bootstraps with a normal venv, the code-server subprocess works as usual, and `debugpy` only ever runs as a listener inside an already-bootstrapped process.
