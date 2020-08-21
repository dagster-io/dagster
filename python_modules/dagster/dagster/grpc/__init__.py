"""Tools for accessing core Dagster APIs over a GRPC mechanism.

GRPC is intended to be used in all cases where host processes communicate with user processes, both
locally (over UDS on MacOS and Unix, and over a local port on Windows) and when communicating with
remote Dagster user proceses (e.g., containers).

The GRPC layer is not intended to supplant the dagster-graphql layer, which should still be used to
drive web frontends like dagit.
"""

from .client import DagsterGrpcClient, ephemeral_grpc_api_client
from .server import DagsterGrpcServer
