---
title: Dagster & SSH/SFTP
sidebar_label: SSH/SFTP
description: Establish encrypted connections to networked resources.
tags:
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ssh
pypi: https://pypi.org/project/dagster-ssh
built_by: Dagster
keywords:
unlisted: false
sidebar_custom_props:
  logo: images/integrations/ssh.svg
partnerlink: https://www.ssh.com/academy/ssh/protocol
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

This integration provides a resource for SSH remote execution using [Paramiko](https://github.com/paramiko/paramiko). It allows you to establish secure connections to networked resources and execute commands remotely. The integration also provides an SFTP client for secure file transfers between the local and remote systems.

### Installation

```bash
pip install dagster-ssh
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/ssh-sftp.py" language="python" />

### About SSH SFTP

The **SSH protocol** allows for secure remote login with strong authentication to networked resources. It protects network connections with strong encryption. The Dagster library provides direct SSH and SFTP calls from within the execution of your pipelines.
