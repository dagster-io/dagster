---
layout: Integration
status: published
name: Bash / Shell
title: Dagster & Bash / Shell
sidebar_label: Bash / Shell
excerpt: Execute a Bash/shell command, directly or as a read from a script file.
date: 2024-08-20
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-shell
docslink:
partnerlink:
logo: /integrations/Shell.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

Dagster comes with a native `PipesSubprocessClient` resource that enables you to launch shell commands directly from Dagster assets and ops. This integration allows you to pass parameters to external shell scripts while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated external execution. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster
```

### Example

<CodeExample filePath="integrations/shell.py" language="python" />

### About shell

A shell is a computer program that presents a command line interface which allows you to control your computer using commands entered with a keyboard instead of controlling graphical user interfaces with a mouse/keyboard/touchscreen combination.
