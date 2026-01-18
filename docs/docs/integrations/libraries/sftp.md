---
title: Dagster & SFTP
sidebar_label: SFTP
sidebar_position: 1
description: >
  The SFTP integration provides a high-performance resource for file transfer operations with support for parallel transfers, batch operations, and advanced filtering capabilities. Built with asyncSSH for optimal performance.
tags: [community-supported]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-sftp
pypi: https://pypi.org/project/dagster-sftp/
sidebar_custom_props:
  logo: images/integrations/sftp.svg
  community: true
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-sftp" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/sftp.py" language="python" />

## About SFTP

SFTP (SSH File Transfer Protocol) is a secure file transfer protocol that provides file access, file transfer, and file management functionalities over a secure SSH connection. It's widely used in enterprise environments for secure data exchange and automated file transfers.
