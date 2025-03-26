---
title: 'uv integration'
sidebar_position: 500
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

To make development easier, particularly with multiple projects, `dg` integrates with the [`uv` package manager](https://docs.astral.sh/uv/).

:::note

We are working on streamlining the configuration of the `uv` integration, and it
is likely to change in the next few releases.

:::

## Default `dg` behavior (`uv run`)

`dg` itself is installed globally and always executes in an isolated environment. However, many `dg` commands need to spawn subprocesses in environments scoped to specific projects. For example, when you run `dg list component-type` in a project directory, `dg` only lists the component types available in that project.

When using `dg` with default settings, the Python subprocess is spawned after detecting a virtual environment in the project directory. This means that, rather than finding the first `python` executable on your shell `PATH`, it will instead use the Python executable from a locally detected virtual environment even if that virtual environment is not currently activated.

By default, `dg` uses a special `uv` command called `uv run` for environment detection and command execution. `uv run` resolves a local virtual environment (`.venv` in an ancestor directory) before running a command, and additionally makes sure that the environment is up to date with the project's specified dependencies before running the command.

`dg`'s use of `uv run` means you don't need to manage global shell state by activating and deactivating virtual environments during development. Instead, `dg` expects (and will scaffold for you) a `.venv` directory in the root of each project, and will use that virtual environment when executing commands (such as `dg scaffold defs` or `dg list component-type`) against that project.

## Disabling use of `uv run`

You can disable `dg`'s use of `uv run` by passing the `--no-use-dg-managed-environment` flag to `dg` commands. This will cause `dg` to still try to resolve local virtual environments by looking up the ancestor tree for `.venv`, but instead launch Python processes directly rather than going through `uv run`.

If you want to opt out of virtual environment detection entirely and just use your ambient Python environment (system Python or an activated virtual env), you should also (a) set `--no-require-local-venv`, and (b) ensure there are no `.venv` directories in
the ancestor tree of your project.

:::info

Disabling `uv` integration with `--no-use-dg-managed-environment` will
currently disable the `dg cache`. This will make some operations noticeably slower.

:::
