---
description: Configure dg from both configuration files and the command line.
sidebar_position: 500
title: Configuring dg
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

`dg` can be configured from both configuration files and the command line.
There are three kinds of settings:

- Application-level settings configure the `dg` application as a whole. They can be set
  in configuration files or on the command line, where they are listed as
  "global options" in the `dg --help` text.
- Project-level settings configure a `dg` project. They can only be
  set in the configuration file for a project.
- Workspace-level settings configure a `dg` workspace. They can only
  be set in the configuration file for a workspace.

:::tip
The application-level settings used in any given invocation of `dg` are the
result of merging settings from one or more configuration files and the command
line. The order of precedence is:

```
user config file < project/workspace config file < command line
```

Note that project and workspace config files are combined above. This is
because, when projects are inside a workspace, application-level settings are
sourced from the workspace configuration file and disallowed in the constituent
project configuration files. In other words, application-level settings are
only allowed in project configuration files if the project is not inside a
workspace.
:::

## Configuration files

There are three kinds of `dg` configuration files: user, project, and workspace.

- [User configuration files](#user-configuration-file) are optional and contain only application-level settings. They are located in a platform-specific location, `~/.dg.toml` (Unix) or `%APPDATA%/dg/dg.toml` (Windows).
- [Project configuration files](#project-configuration-file) are required to mark a directory as a `dg` project. They are located in the root of a `dg` project and contain project-specific settings. They may also contain application-level settings if the project is not inside a workspace.
- [Workspace configuration files](#workspace-configuration-file) are required to mark a directory as a `dg` workspace. They are located in the root of a `dg` workspace and contain workspace-specific settings. They may also contain application-level settings. When projects are inside a workspace, the application-level settings of the workspace apply to all contained projects as well.

When `dg` is launched, it will attempt to discover all three configuration files by looking up the directory hierarchy from the CWD (and in the dedicated location for user configuration files). Many commands require a project or workspace to be in scope. If the corresponding configuration file is not found when launching such a command, `dg` will raise an error.

### User configuration file

A user configuration file can be placed at `~/.dg.toml` (Unix) or
`%APPDATA%/dg/dg.toml` (Windows).

Below is an example of a user configuration file. The `cli` section contains
application-level settings and is the only permitted section. The settings
listed in the below sample are comprehensive:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/configuring-dg/user-config.toml"
  title=".dg.toml"
  language="toml"
/>

### Project configuration file

A project configuration file is located in the root of a `dg` project. It may
either be a `pyproject.toml` file or a `dg.toml` file. If it is a
`pyproject.toml`, then all settings are nested under the `tool.dg` key. If it
is a `dg.toml` file, then settings should be placed at the top level. Usually
`pyproject.toml` is used for project configuration.

Below is an example of the dg-scoped part of a `pyproject.toml` (note all settings are part of `tool.dg.*` tables) for a project named `my-project`. The `tool.dg.project` section is a comprehensive list of supported settings:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/configuring-dg/project-config.toml"
  title="pyproject.toml"
  language="toml"
/>

### Workspace configuration file

A workspace configuration file is located in the root of a `dg` workspace. It
may either be a `pyproject.toml` file or a `dg.toml` file. If it is a `pyproject.toml`,
then all settings are nested under the `tool.dg` key. If it is a `dg.toml` file,
then all settings are top-level keys. Usually `dg.toml` is used for workspace
configuration.

Below is an example of a `dg.toml` file for a workspace. The
`workspace` section is a comprehensive list of supported settings:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/configuring-dg/workspace-config.toml"
  title="dg.toml"
  language="toml"
/>
