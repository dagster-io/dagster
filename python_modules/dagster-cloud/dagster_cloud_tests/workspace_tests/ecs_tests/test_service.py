from dagster_cloud.workspace.ecs.client import Client
from dagster_cloud.workspace.ecs.service import Service


def test_arn():
    short_arn = "arn:aws:ecs:us-east-1:1234567890:service/service-name"
    long_arn = "arn:aws:ecs:us-east-1:1234567890:service/cluster-name/service-name"

    client = Client(
        cluster_name="cluster-name",
        service_discovery_namespace_id="fake-namespace",
        log_group="fake-log-group",
    )

    service = Service(client=client, arn=short_arn)
    assert service.arn == long_arn

    service = Service(client=client, arn=long_arn)
    assert service.arn == long_arn
