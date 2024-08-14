from dagster import asset, Definitions, AssetExecutionContext
from dagster_ssh import SSHResource


sftp_resource = SSHResource(
    remote_host="your.server.com",
    remote_port=2121,
    username="your-username",
    password="your-password",  # or use 'key_file': 'path/to/id_rsa' for key-based authentication

)


@asset
def sftp_file(context: AssetExecutionContext, sftp: SSHResource):
    local_file_path = "sftp_example_file.txt"
    remote_file_path = "/path/to/remote/file.txt"
    sftp.sftp_put(local_file_path, remote_file_path)
    context.log.info(f"Uploaded {local_file_path} to {remote_file_path} on SFTP server")


defs = Definitions(
    assets=[sftp_file],
    resources={
        "sftp": sftp_resource,
    },
)
