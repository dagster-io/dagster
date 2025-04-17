---
title: Dagster & GitHub
sidebar_label: GitHub
description: Integrate with GitHub Apps and automate operations within your github repositories.
tags:
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-github
pypi: https://pypi.org/project/dagster-github/
built_by: Dagster
keywords:
unlisted: false
sidebar_custom_props:
  logo: images/integrations/github.svg
partnerlink: https://github.com/
---

import Deprecated from '@site/docs/partials/\_Deprecated.md';

<Deprecated />

This library provides an integration with _[GitHub Apps](https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps)_ by providing a thin wrapper on the GitHub v4 GraphQL API. This allows for automating operations within your GitHub repositories and with the tighter permissions scopes that GitHub Apps allow for vs using a personal token.

### Installation

```bash
pip install dagster-github
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/github.py" language="python" />

### About GitHub

**GitHub** provides a highly available git repo, access control, bug tracking, software feature requests, task management, continuous integration, and wikis for open source and commercial projects.
