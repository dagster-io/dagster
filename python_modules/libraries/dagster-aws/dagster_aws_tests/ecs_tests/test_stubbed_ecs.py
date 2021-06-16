def test_register_task_definition(ecs):
    response = ecs.register_task_definition(family="dagster", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:1")

    response = ecs.register_task_definition(family="other", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "other"
    assert response["taskDefinition"]["revision"] == 1
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("other:1")

    response = ecs.register_task_definition(family="dagster", containerDefinitions=[])
    assert response["taskDefinition"]["family"] == "dagster"
    assert response["taskDefinition"]["revision"] == 2
    assert response["taskDefinition"]["taskDefinitionArn"].endswith("dagster:2")

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[{"image": "hello_world:latest"}]
    )
    assert response["taskDefinition"]["containerDefinitions"][0]["image"] == "hello_world:latest"

    response = ecs.register_task_definition(
        family="dagster", containerDefinitions=[], networkMode="bridge"
    )
    assert response["taskDefinition"]["networkMode"] == "bridge"
