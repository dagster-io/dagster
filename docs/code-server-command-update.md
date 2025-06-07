# Dagster Code-Server Command Documentation Update

## Overview

The `dagster code-server` command is an experimental CLI command used to run a code server that supports hot-reloading of code locations when new code is deployed. This command is distinct from the `dagster api grpc` command, although some parameters may appear similar.

## Usage

```bash
dagster code-server [OPTIONS]
```

### Key Features

- Enables hot-reloading of code locations without restarting the entire Dagster instance.
- Useful during development for faster iteration cycles.
- Currently marked as experimental and may change in future releases.

## Differences from `dagster api grpc`

- `dagster api grpc` is the documented and stable command for running the Dagster gRPC API server.
- `dagster code-server` focuses on code location hot-reloading and is intended primarily for development use.
- Parameter sets may differ; users should consult the command help for the most accurate options.

## When to Use

- Use `dagster code-server` during active development when you want to see code changes reflected immediately.
- Use `dagster api grpc` for production or stable API serving.

## Status

- Experimental: The command is still under active development and may have breaking changes.
- Users should monitor the Dagster release notes and documentation for updates.

---

For more information, please refer to the official Dagster documentation and community channels.
