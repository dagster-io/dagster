from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import boto3.session
import botocore.client

from dagster_aws.utils import ResourceWithBoto3Configuration, construct_boto_client_retry_config

if TYPE_CHECKING:
    import botocore


class RDSResource(ResourceWithBoto3Configuration):
    """A resource for interacting with the AWS RDS service.

    It wraps both the AWS RDS client (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html),
    and the AWS RDS Data client (https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds-data.html).

    The AWS-RDS client (``RDSResource.get_rds_client()``) allows access to the management layer of RDS (creating, starting, configuring databases).
    The AWS RDS Data (``RDSResource.get_data_client``) allows executing queries on the SQL databases themselves.
    Note that AWS RDS Data service is only available for Aurora database. For accessing data from other types of RDS databases,
    you should directly use the corresponding SQL client instead (e.g. Postgres/MySQL).


    Example:
        .. code-block:: python

            from dagster import Definitions, asset
            from dagster_aws.rds import RDSResource

            @asset
            def my_table(rds_resource: RDSResource):
                with rds_resource.get_rds_client() as rds_client:
                    rds_client.describe_db_instances()['DBInstances']
                with rds_resource.get_data_client() as data_client:
                    data_client.execute_statement(
                        resourceArn="RESOURCE_ARN",
                        secretArn="SECRET_ARN",
                        sql="SELECT * from mytable",
                    )

            defs = Definitions(
                assets=[my_table],
                resources={
                    "rds_resource": RDSResource(
                        region_name="us-west-1"
                    )
                }
            )

    """

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def _create_rds_client(self, client_type: str) -> Any:
        session = boto3.session.Session(profile_name=self.profile_name)
        return session.client(
            client_type,
            region_name=self.region_name,
            use_ssl=self.use_ssl,
            verify=self.verify,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
            config=construct_boto_client_retry_config(self.max_attempts),
        )

    @contextmanager
    def get_rds_client(self) -> Generator["botocore.client.rds", None, None]:  # pyright: ignore (reportAttributeAccessIssue)
        yield self._create_rds_client("rds")

    @contextmanager
    def get_data_client(self) -> Generator["botocore.client.rds_data", None, None]:  # pyright: ignore (reportAttributeAccessIssue)
        yield self._create_rds_client("rds-data")
