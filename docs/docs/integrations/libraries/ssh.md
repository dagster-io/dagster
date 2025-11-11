---
title: Dagster & SSH
sidebar_label: SSH
description: This integration provides a resource for SSH remote execution using Paramiko. It allows you to establish secure connections to networked resources and execute commands remotely. The integration also provides an SFTP client for secure file transfers between the local and remote systems.
tags: [dagster-supported]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ssh
pypi: https://pypi.org/project/dagster-ssh
sidebar_custom_props:
  logo: images/integrations/ssh.svg
partnerlink: https://www.ssh.com/academy/ssh/protocol
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-ssh" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/ssh.py" language="python" />

## About SSH

The **SSH protocol** allows for secure remote login with strong authentication to networked resources. It protects network connections with strong encryption. The Dagster library provides direct SSH and SFTP calls from within the execution of your pipelines.
