def test_default_instance(instance_cm):
    with instance_cm() as instance:
        assert instance.run_launcher.use_current_task_definition


def test_dont_use_current_task_definition(instance_cm):

    sidecars = [
        {
            "name": "DatadogAgent",
            "image": "public.ecr.aws/datadog/agent:latest",
            "environment": [
                {"name": "ECS_FARGATE", "value": "true"},
            ],
        }
    ]

    with instance_cm(
        config={
            "use_current_task_definition": False,
            "cluster": "my-ecs-cluster",
            "subnets": ["subnet1", "subnet2"],
            "execution_role_arn": "fake-role",
            "task_role_arn": "other-fake-role",
            "log_group": "my_log_group",
            "sidecar_container_definitions": sidecars,
        }
    ) as instance:
        launcher = instance.run_launcher
        assert launcher.cluster == "my-ecs-cluster"
        assert launcher.subnets == ["subnet1", "subnet2"]
        assert launcher.execution_role_arn == "fake-role"
        assert launcher.log_group == "my_log_group"
        assert launcher.sidecar_container_definitions == sidecars
