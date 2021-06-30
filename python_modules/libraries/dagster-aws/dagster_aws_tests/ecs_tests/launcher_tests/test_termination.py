def test_termination(instance, pipeline, external_pipeline):
    run = instance.create_run_for_pipeline(pipeline)

    assert not instance.run_launcher.can_terminate(run.run_id)

    instance.launch_run(run.run_id, external_pipeline)

    assert instance.run_launcher.can_terminate(run.run_id)
    assert instance.run_launcher.terminate(run.run_id)
    assert not instance.run_launcher.can_terminate(run.run_id)
    assert not instance.run_launcher.terminate(run.run_id)
