from dagster import AssetExecutionContext, Definitions, asset
from dagster_ssh import SSHResource

sftp_resource = SSHResource(
    remote_host="your.hostname",
    remote_port=22,
    username="example",
    key_file="/Users/example/.ssh/id_ed25519",
)


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
