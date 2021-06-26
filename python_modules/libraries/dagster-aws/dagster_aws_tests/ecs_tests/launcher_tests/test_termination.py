def test_termination(instance, workspace, run):

    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.launch_run(run.run_id, workspace)

    assert instance.run_launcher.can_terminate(run.run_id)
    assert instance.run_launcher.terminate(run.run_id)
    assert not instance.run_launcher.can_terminate(run.run_id)
    assert not instance.run_launcher.terminate(run.run_id)
