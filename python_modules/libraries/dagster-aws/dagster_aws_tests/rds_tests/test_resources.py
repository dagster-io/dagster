from unittest.mock import MagicMock, patch

from pprint import pprint
from dagster import asset, materialize_to_memory
from dagster_aws.rds import RDSResource

def test_rds_resource(mock_rds_client, mock_rds_data_client):
    @asset
    def rds_asset(rds_resource: RDSResource):
        with rds_resource.get_rds_client() as rds_client:
            rds_client.create_db_instance(
                DBInstanceIdentifier='test-instance',
                MasterUsername='admin',
                MasterUserPassword='password',
                DBInstanceClass='db.t2.micro',
                Engine='postgres'
            )
            db_instances = rds_client.describe_db_instances()["DBInstances"]
            pprint(db_instances)
            assert len(db_instances) == 1

    @asset
    def rds_data_asset(rds_resource: RDSResource):
        with rds_resource.get_data_client() as rds_data_client:
            rds_data_client.execute_statement(
                resourceArn="arn:aws:rds:us-east-1:example:cluster:database-1",
                secretArn="arn:aws:secretsmanager:us-east-1:example:secret:rds!cluster-1",
                sql="SELECT * from mytable",
            )
            
    result = materialize_to_memory(
        [rds_asset, rds_data_asset],
        resources={
            "rds_resource": RDSResource(
                region_name="us-east-1"
            )
        },
    )

    assert result.success
