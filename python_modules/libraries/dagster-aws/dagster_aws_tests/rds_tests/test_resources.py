import requests
from dagster import asset, materialize_to_memory

from dagster_aws.rds import RDSResource


def configure_moto_mock_response():
    mock_response = {
        "results": [
            {
                "records": [
                    [{"stringValue": "title1"}, {"longValue": 2001}],
                    [{"stringValue": "title2"}, {"longValue": 2010}],
                ],
                "numberOfRecordsUpdated": 0,
            }
        ]
    }

    # moto is configured through HTTP: https://docs.getmoto.org/en/stable/docs/services/rds-data.html
    resp = requests.post(
        "http://motoapi.amazonaws.com/moto-api/static/rds-data/statement-results",
        json=mock_response,
    )
    assert resp.status_code == 201


def test_rds_resource(mock_rds_client, mock_rds_data_client):
    @asset
    def rds_asset(rds_resource: RDSResource):
        with rds_resource.get_rds_client() as rds_client:
            rds_client.create_db_instance(
                DBInstanceIdentifier="test-instance",
                MasterUsername="admin",
                MasterUserPassword="password",
                DBInstanceClass="db.t2.micro",
                Engine="postgres",
            )
            db_instances = rds_client.describe_db_instances()["DBInstances"]
            assert len(db_instances) == 1

    @asset
    def rds_data_asset(rds_resource: RDSResource):
        configure_moto_mock_response()

        with rds_resource.get_data_client() as rds_data_client:
            response = rds_data_client.execute_statement(
                resourceArn="arn:aws:rds:us-east-1:123456789012:cluster:database-1",
                secretArn="arn:aws:secretsmanager:us-east-1:123456789012:secret:rds!cluster-1",
                sql="SELECT * from films;",
            )

            assert len(response["records"]) == 2

    result = materialize_to_memory(
        [rds_asset, rds_data_asset],
        resources={"rds_resource": RDSResource(region_name="us-east-1")},
    )

    assert result.success
