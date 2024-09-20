---
title: "Load a file to an SFTP server with Dagster"
description: "This use case demonstrates how to transfer a file to an SFTP server using Dagster. The objective is to automate the process of uploading files to an SFTP server for secure storage or further processing."
tags: ["sftp", "file transfer"]
---

# Load a file to an SFTP server with Dagster

This use case demonstrates how to transfer a file to an SFTP server using Dagster. The objective is to automate the process of uploading files to an SFTP server for secure storage or further processing.

---

## What You'll Learn

You will learn how to:

- Define a Dagster asset that uploads a file to an SFTP server
- Configure the SFTP resource in Dagster
- Implement the asset to perform the file upload

---

## Prerequisites

To follow the steps in this guide, you will need:

- To have Dagster installed. Refer to the [Dagster Installation Guide](https://docs.dagster.io/getting-started/installation) for instructions.
- A basic understanding of Dagster. Refer to the [Dagster Documentation](https://docs.dagster.io/getting-started/what-why-dagster) for more information.
- Access to an SFTP server with appropriate credentials.

---

## Steps to Implement With Dagster

By following these steps, you will have a Dagster asset that successfully uploads a file to an SFTP server. This allows you to automate file transfers securely.

### Step 1: Install the SSH integration

```shell
pip install dagster-ssh
```

### Step 1: Define the SFTP Resource

First, define the SFTP resource that will be used to connect to the SFTP server.

```python
from dagster import Definitions
from dagster_ssh import SSHResource


sftp_resource = SSHResource(
    remote_host="your.hostname",
    remote_port=22,
    username="example",
    key_file="/Users/example/.ssh/id_ed25519",
)

defs = Definitions(
    resources={
        'sftp': sftp_resource,
    }
)
```

### Step 2: Create the asset to upload the file

Next, create a Dagster asset that uses the SFTP resource to upload a file.

```python
from dagster import AssetExecutionContext, asset
from dagster_ssh import SSHResource


@asset
def sftp_file(context: AssetExecutionContext, sftp: SSHResource):
    local_file_path = "hello.txt"
    remote_file_path = "/path/to/destination/hello.txt"
    sftp.sftp_put(local_file_path, remote_file_path)
    context.log.info(f"Uploaded {local_file_path} to {remote_file_path} on SFTP server")


defs = Definitions(
    assets=[sftp_file],
    resources={
        "sftp": sftp_resource,
    },
)
```

---

## Expected Outcomes

By implementing this use case, you will have an automated process for uploading files to an SFTP server using Dagster. This can be used for secure file transfers, backups, or any other scenario where files need to be uploaded to an SFTP server.

---

## Troubleshooting

- **Connection Issues**: Ensure that the SFTP server address, username, and password (or key file) are correct.
- **File Not Found**: Verify that the local file path is correct and that the file exists.
- **Permission Denied**: Ensure that the user has the necessary permissions to upload files to the specified remote directory.

---

## Next Steps

- Explore how to download files from an SFTP server using Dagster.
- Integrate this asset into a larger data pipeline that processes the uploaded files.

---

## Additional Resources

- [Dagster SSH Integration Documentation](https://docs.dagster.io/integrations/dagster-ssh-sftp)
- [Dagster Documentation](https://docs.dagster.io)
- [Dagster Community Slack](https://dagster.io/slack)
