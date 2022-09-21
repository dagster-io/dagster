from dagster_aws.ecs.tasks import DagsterEcsTaskDefinitionConfig


def test_create_dagster_task_definition_dict():
    task_config = DagsterEcsTaskDefinitionConfig(
        family="my_task",
        image="foo_image:bar",
        container_name="run",
        command=["dagster", "api", "execute_run"],
        execution_role_arn="fake-role",
        log_configuration={
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "my-log-group",
                "awslogs-region": "us_east_=",
                "awslogs-stream-prefix": "my_task",
            },
        },
        task_role_arn="fake-task-role",
        environment=[
            {
                "name": "FOO_ENV_VAR",
                "value": "BAR_VALUE",
            }
        ],
        secrets=[
            {
                "name": "FOO_SECRET",
                "valueFrom": "BAR_SECRET_VALUE",
            }
        ],
        sidecars=[
            {
                "name": "DatadogAgent",
                "image": "public.ecr.aws/datadog/agent:latest",
                "environment": [
                    {"name": "ECS_FARGATE", "value": "true"},
                ],
            }
        ],
    )

    assert task_config.task_definition_dict("FARGATE") == {
        "family": "my_task",
        "requiresCompatibilities": ["FARGATE"],
        "networkMode": "awsvpc",
        "containerDefinitions": [
            {
                "name": "run",
                "image": "foo_image:bar",
                "environment": [{"name": "FOO_ENV_VAR", "value": "BAR_VALUE"}],
                "command": ["dagster", "api", "execute_run"],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "my-log-group",
                        "awslogs-region": "us_east_=",
                        "awslogs-stream-prefix": "my_task",
                    },
                },
                "secrets": [{"name": "FOO_SECRET", "valueFrom": "BAR_SECRET_VALUE"}],
            },
            {
                "name": "DatadogAgent",
                "image": "public.ecr.aws/datadog/agent:latest",
                "environment": [
                    {"name": "ECS_FARGATE", "value": "true"},
                ],
            },
        ],
        "executionRoleArn": "fake-role",
        "cpu": "256",
        "memory": "512",
        "taskRoleArn": "fake-task-role",
    }

    assert task_config.task_definition_dict("EC2")["requiresCompatibilities"] == []
