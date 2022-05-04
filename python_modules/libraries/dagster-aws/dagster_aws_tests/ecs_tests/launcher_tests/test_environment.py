def test_environment_with_container_context(
    ecs,
    instance_cm,
    launch_run_with_container_context,
):
    initial_task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]

    # Secrets config is pulled from container context on the run, rather than run launcher config
    config = {
        "environment": [{"name": "foo", "value": "bar"}],
    }

    with instance_cm(config) as instance:
        launch_run_with_container_context(instance)

    # A new task definition is created
    task_definitions = ecs.list_task_definitions()["taskDefinitionArns"]
    assert len(task_definitions) == len(initial_task_definitions) + 1
    task_definition_arn = list(set(task_definitions).difference(initial_task_definitions))[0]
    task_definition = ecs.describe_task_definition(taskDefinition=task_definition_arn)
    task_definition = task_definition["taskDefinition"]

    # It includes environment vars
    environment = task_definition["containerDefinitions"][0]["environment"]
    assert environment[0] == {
        "name": config["environment"][0]["name"],
        "value": config["environment"][0]["value"],
    }

    # But no other env vars
    assert len(environment) == 1
