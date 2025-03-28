import lakefs_client
from lakefs_client import models
from lakefs_client.client import LakeFSClient

import dagster as dg

logger = dg.get_dagster_logger()

configuration = lakefs_client.Configuration()
configuration.username = "AAAA"
configuration.password = "BBBBB"
configuration.host = "https://my-org.us-east-1.lakefscloud.io"


@dg.asset
def create_branch(client: dg.ResourceParam[LakeFSClient]):
    branch_id = client.branches.create_branch(
        repository="test-repo",
        branch_creation=models.BranchCreation(name="experiment", source="main"),
    )
    logger.info(branch_id)


@dg.asset(deps=[create_branch])
def list_branches(client: dg.ResourceParam[LakeFSClient]):
    list_branches = client.branches.list_branches(repository="test-repo")
    logger.info(list_branches)


defs = dg.Definitions(
    assets=[create_branch, list_branches],
    resources={"client": LakeFSClient(configuration)},
)
