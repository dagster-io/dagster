---
title: Dagster & SSH
sidebar_label: SSH
sidebar_position: 1
description: This integration provides a resource for SSH remote execution using Paramiko. It allows you to establish secure connections to networked resources and execute commands remotely. The integration also provides an SFTP client for secure file transfers between the local and remote systems.
tags: [dagster-supported, other]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ssh
pypi: https://pypi.org/project/dagster-ssh
sidebar_custom_props:
  logo: images/integrations/ssh.svg
partnerlink: https://www.ssh.com/academy/ssh/protocol
canonicalUrl: '/integrations/libraries/ssh'
slug: '/integrations/libraries/ssh'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-ssh" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/ssh.py" language="python" />

## Host key verification

`SSHResource` verifies the remote host's key before it sends any credentials, for connections, SFTP transfers, and tunnels from `get_tunnel`. It trusts the keys in `/etc/ssh/ssh_known_hosts`, `~/.ssh/known_hosts`, and the optional `known_hosts_file`, and rejects a host that is not listed there, that presents a key different from its entry, or that presents a key marked `@revoked`. Lines marked `@cert-authority` are skipped, because host certificates are not supported. For a connection or SFTP transfer, the error names the host, its key type, and its fingerprint. `get_tunnel` checks known_hosts before it connects, so its error for an unlisted host names only the host. To trust a host, add its key to a known_hosts file, for example with `ssh-keyscan -p 22 example.com >> ~/.ssh/known_hosts`, after you confirm the fingerprint with the host's administrator.

Setting `no_host_key_check=True` accepts a host that is not in known_hosts and skips known_hosts files that cannot be read. A host that is listed still has to present a listed key that is not revoked. For a host that is not listed, a machine on the network can impersonate the host and receive your credentials, so use this only for hosts you trust at the network level, such as a throwaway test server.

## About SSH

The **SSH protocol** allows for secure remote login with strong authentication to networked resources. It protects network connections with strong encryption. The Dagster library provides direct SSH and SFTP calls from within the execution of your pipelines.
