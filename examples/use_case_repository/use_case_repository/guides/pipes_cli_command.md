---
title: "Using Dagster Pipes Subprocess to Run a CLI Command"
description: "This use case demonstrates how to use Dagster Pipes to run a CLI command within a Dagster asset. The objective is to execute non-Python workloads and integrate their outputs into Dagster's data pipeline."
tags: ["dagster pipes", "subprocess"]
---

# Running CLI Commands with Dagster Pipes

This guide demonstrates how to use Dagster Pipes to run a CLI command within a Dagster asset. This is useful for integrating non-Python workloads, such as Bash scripts or other command-line tools, into your Dagster data pipeline.

---

## What You’ll Learn

You will learn how to:

- Define a Dagster asset that invokes a CLI command.
- Use Dagster Pipes to manage subprocess execution.
- Capture and use the output of the CLI command within Dagster.

---

## Prerequisites

To follow the steps in this guide, you'll need:

- To have Dagster and the Dagster UI (`dagster-webserver`) installed. Refer to the [Installation guide](https://docs.dagster.io/getting-started/install) for more info.

---

## Steps to Implement with Dagster

By following these steps, you will have a Dagster asset that successfully runs a CLI command and logs its output. This allows you to integrate non-Python workloads into your Dagster data pipeline.

### Step 1: Define the CLI Command Script

Create a script that contains the CLI command you want to run. For example, create a file named `external_script.sh` with the following content:

```bash
#!/bin/bash
echo "Hello from CLI"
echo "My env var is: ${MY_ENV_VAR}"
```

### Step 2: Define the Dagster Asset

Define a Dagster asset that uses `PipesSubprocessClient` to run the CLI command. Include any necessary environment variables or additional parameters.

Save the following file to `dagster_pipes_cli.py`:

```python
import shutil

from dagster import AssetExecutionContext, Definitions, PipesSubprocessClient, asset

@asset
def cli_command_asset(
    context: AssetExecutionContext, pipes_subprocess_client: PipesSubprocessClient
):
    cmd = [shutil.which("bash"), "external_script.sh"]
    return pipes_subprocess_client.run(
        command=cmd,
        context=context,
        env={"MY_ENV_VAR": "example_value"},
    ).get_materialize_result()

defs = Definitions(
    assets=[cli_command_asset],
    resources={"pipes_subprocess_client": PipesSubprocessClient()},
)
```

### Step 3: Configure and Run the Asset

Ensure the script is executable and run the Dagster asset to see the output.

```bash
chmod +x external_script.sh
dagster dev -f path_to_your_dagster_file.py
```

---

## Troubleshooting

- **Permission Denied**: Ensure the script file has executable permissions using `chmod +x`.
- **Command Not Found**: Verify the command is available in the system's `PATH` or provide the full path to the command.

---

## Next Steps

Explore more advanced use cases with Dagster Pipes, such as integrating with other command-line tools or handling more complex workflows.

---

## Additional Resources

- [Dagster Pipes Documentation](https://docs.dagster.io/guides/dagster-pipes)
- [Dagster Installation Guide](https://docs.dagster.io/getting-started/install)
