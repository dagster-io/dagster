---
layout: Integration
status: published
name: SSH/SFTP
title: Dagster & SSH/SFTP
sidebar_label: SSH/SFTP
excerpt: Establish encrypted connections to networked resources.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-ssh
docslink: 
partnerlink: https://www.ssh.com/academy/ssh/protocol
logo: /integrations/SSH.svg
categories:
  - Other
enabledBy:
enables:
---

### About this integration

This integration provides a resource for SSH remote execution using [Paramiko](https://github.com/paramiko/paramiko). It allows you to establish secure connections to networked resources and execute commands remotely. The integration also provides an SFTP client for secure file transfers between the local and remote systems.

### Installation

```bash
pip install dagster-ssh
```

### Example

```python
import dagster as dg
from dagster_ssh import SSHResource


@dg.asset
def ssh_asset(ssh: SSHResource):
    ssh.sftp_get("/path/to/remote.csv", "path/to/local.csv")


defs = dg.Definitions(
    assets=[ssh_asset],
    resources={"ssh": SSHResource(remote_host="foo.com", key_file="path/to/id_rsa")},
)

```

### About SSH SFTP

The **SSH protocol** allows for secure remote login with strong authentication to networked resources. It protects network connections with strong encryption. The Dagster library provides direct SSH and SFTP calls from within the execution of your pipelines.
