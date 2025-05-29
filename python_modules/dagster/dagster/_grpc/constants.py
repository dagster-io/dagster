from collections.abc import Sequence
from enum import Enum

INCREASE_TIMEOUT_DAGSTER_YAML_MSG = """To increase the timeout, add the following to a dagster.yaml file, located in your $DAGSTER_HOME folder or the folder where you are running `dagster dev`:

code_servers:
  local_startup_timeout: <timeout value>

"""


class GrpcServerCommand(Enum):
    API_GRPC = "api_grpc"
    CODE_SERVER_START = "code_server_start"

    @property
    def server_command(self) -> Sequence[str]:
        return (
            ["api", "grpc", "--lazy-load-user-code"]
            if self == GrpcServerCommand.API_GRPC
            else ["code-server", "start"]
        )
