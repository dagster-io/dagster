def test_termination(instance, workspace, run):
    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.launch_run(run.run_id, workspace)

    assert instance.run_launcher.can_terminate(run.run_id)
    assert instance.run_launcher.terminate(run.run_id)
    assert not instance.run_launcher.can_terminate(run.run_id)
    assert not instance.run_launcher.terminate(run.run_id)


def test_missing_run(instance, workspace, run, monkeypatch):
    instance.launch_run(run.run_id, workspace)

    def missing_run(*_args, **_kwargs):
        return None

    original = instance.get_run_by_id

    monkeypatch.setattr(instance, "get_run_by_id", missing_run)
    assert not instance.run_launcher.can_terminate(run.run_id)

    monkeypatch.setattr(instance, "get_run_by_id", original)
    assert instance.run_launcher.can_terminate(run.run_id)

    monkeypatch.setattr(instance, "get_run_by_id", missing_run)
    assert not instance.run_launcher.terminate(run.run_id)

    monkeypatch.setattr(instance, "get_run_by_id", original)
    assert instance.run_launcher.terminate(run.run_id)


def test_missing_tag(instance, workspace, run):
    instance.launch_run(run.run_id, workspace)
    original = instance.get_run_by_id(run.run_id).tags

    instance.add_run_tags(run.run_id, {"ecs/task_arn": ""})
    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.add_run_tags(run.run_id, original)
    instance.add_run_tags(run.run_id, {"ecs/cluster": ""})
    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.add_run_tags(run.run_id, original)
    assert instance.run_launcher.can_terminate(run.run_id)

    instance.add_run_tags(run.run_id, {"ecs/task_arn": ""})
    assert not instance.run_launcher.terminate(run.run_id)

    instance.add_run_tags(run.run_id, original)
    instance.add_run_tags(run.run_id, {"ecs/cluster": ""})
    assert not instance.run_launcher.terminate(run.run_id)

    instance.add_run_tags(run.run_id, original)
    assert instance.run_launcher.terminate(run.run_id)


def test_eventual_consistency(instance, workspace, run, monkeypatch):
    instance.launch_run(run.run_id, workspace)

    def empty(*_args, **_kwargs):
        return {"tasks": []}

    original = instance.run_launcher.ecs.describe_tasks

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", empty)
    assert not instance.run_launcher.can_terminate(run.run_id)

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", original)
    assert instance.run_launcher.can_terminate(run.run_id)

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", empty)
    assert not instance.run_launcher.terminate(run.run_id)

    monkeypatch.setattr(instance.run_launcher.ecs, "describe_tasks", original)
    assert instance.run_launcher.terminate(run.run_id)
