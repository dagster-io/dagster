import logging

from dagster._utils.cached_method import cached_method


class Service:
    def __init__(self, client, arn):
        self.client = client
        self.arn = self._long_arn(arn)
        self.name = arn.split("/")[-1]

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.arn == other.arn

    def __hash__(self) -> int:
        return hash(self.arn)

    def __str__(self) -> str:
        return self.arn

    @property
    def hostname(self):
        hostname = f"{self.name}.{self.client.namespace}"
        return hostname

    @property
    def tags(self):
        if not self.service_discovery_arn:
            return {}

        try:
            tags = self.client.service_discovery.list_tags_for_resource(
                ResourceARN=self.service_discovery_arn
            ).get("Tags")
        except self.client.service_discovery.exceptions.ResourceNotFoundException:
            logging.warning(f"Could not find service discovery ARN {self.service_discovery_arn}")
            return {}

        return dict([(tag["Key"], tag["Value"]) for tag in tags])

    @property
    @cached_method
    def service_discovery_arn(self):
        service = self.client.ecs.describe_services(
            cluster=self.client.cluster_name,
            services=[self.arn],
        ).get("services", [{}])[0]

        registries = service.get("serviceRegistries") or [{}]
        arn = registries[0].get("registryArn")

        return arn

    @property
    @cached_method
    def public_ip(self):
        task_arns = self.client.ecs.list_tasks(
            cluster=self.client.cluster_name,
            serviceName=self.name,
        ).get("taskArns")

        # Assume there's only one task per service
        task = self.client.ecs.describe_tasks(
            cluster=self.client.cluster_name,
            tasks=task_arns,
        ).get("tasks")[0]

        # Assume there's only one attachment per task
        attachment_details = task.get("attachments")[0].get("details")
        for detail in attachment_details:
            if detail.get("name") == "networkInterfaceId":
                eni_id = detail.get("value")
                eni = self.client.ec2.NetworkInterface(eni_id)
                if eni.association_attribute:
                    return eni.association_attribute.get("PublicIp")

    @property
    @cached_method
    def create_timestamp(self) -> float | None:
        response = self.client.ecs.describe_services(
            cluster=self.client.cluster_name, services=[self.name]
        )

        service_description = response["services"][0]

        # Extract the creation timestamp
        return service_description["createdAt"].timestamp()

    @property
    @cached_method
    def environ(self):
        task_arns = self.client.ecs.list_tasks(
            cluster=self.client.cluster_name,
            serviceName=self.name,
        ).get("taskArns")

        # Assume there's only one task per service
        task = self.client.ecs.describe_tasks(
            cluster=self.client.cluster_name,
            tasks=task_arns,
        ).get("tasks")[0]

        # Assume there's only one container per task
        task_definition_arn = task.get("taskDefinitionArn")
        container = self.client.ecs.describe_task_definition(taskDefinition=task_definition_arn)[
            "taskDefinition"
        ]["containerDefinitions"][0]
        return dict((env["name"], env["value"]) for env in container["environment"])

    def _long_arn(self, arn):
        # https://docs.aws.amazon.com/AmazonECS/latest/userguide/ecs-account-settings.html#ecs-resource-ids
        arn_parts = arn.split("/")
        if len(arn_parts) == 3:
            # A new long arn:
            # arn:aws:ecs:region:aws_account_id:service/cluster-name/service-name
            # Return it as is
            return arn
        else:
            # An old short arn:
            # arn:aws:ecs:region:aws_account_id:service/service-name
            # Add the cluster name
            return "/".join([arn_parts[0], self.client.cluster_name, arn_parts[1]])
