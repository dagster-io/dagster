---
layout: Integration
status: published
name: GitHub
title: Dagster & GitHub
sidebar_label: GitHub
excerpt: Integrate with GitHub Apps and automate operations within your github repositories.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-github
docslink:
partnerlink: https://github.com/
categories:
  - Other
enabledBy:
enables:
tags: [dagster-supported]
sidebar_custom_props: 
  logo: images/integrations/github.svg
---

import Deprecated from '../../partials/\_Deprecated.md';

<Deprecated />

This library provides an integration with _[GitHub Apps](https://docs.github.com/en/developers/apps/getting-started-with-apps/about-apps)_ by providing a thin wrapper on the GitHub v4 GraphQL API. This allows for automating operations within your GitHub repositories and with the tighter permissions scopes that GitHub Apps allow for vs using a personal token.

### Installation

```bash
pip install dagster-github
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/github.py" language="python" />

### About GitHub

**GitHub** provides a highly available git repo, access control, bug tracking, software feature requests, task management, continuous integration, and wikis for open source and commercial projects.
