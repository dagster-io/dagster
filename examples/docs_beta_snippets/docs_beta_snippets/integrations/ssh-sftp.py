from dagster_ssh import SSHResource

import dagster as dg


@dg.asset
def ssh_asset(ssh: SSHResource):
    ssh.sftp_get("/path/to/remote.csv", "path/to/local.csv")


defs = dg.Definitions(
    assets=[ssh_asset],
    resources={"ssh": SSHResource(remote_host="foo.com", key_file="path/to/id_rsa")},
)
