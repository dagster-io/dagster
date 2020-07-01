from contextlib import contextmanager

from dagster import PipelineRun, execute_pipeline, execute_pipeline_iterator, pipeline, solid
from dagster.seven import mock


@solid
def noop_solid(_):
    pass


@pipeline
def noop_pipeline():
    noop_solid()


@contextmanager
def assert_no_warnings():
    with mock.patch('warnings.warn') as warn_mock:
        yield
        acceptable_warnings = []  # can add warnings here while doing renames
        for call in warn_mock.call_args_list:
            assert any(warning in call[0][0] for warning in acceptable_warnings), call


def test_warnings_execute_pipeline():
    assert execute_pipeline(noop_pipeline).success

    with mock.patch('warnings.warn') as warn_mock:
        assert execute_pipeline(noop_pipeline, environment_dict={}).success
        warn_mock.assert_any_call(
            '"environment_dict" is deprecated and will be removed in 0.9.0, '
            'use "run_config" instead.',
            stacklevel=6,
        )


def test_no_warnings_execute_pipeline():
    # flush out unrelated warnings
    assert execute_pipeline(noop_pipeline).success

    with assert_no_warnings():
        assert execute_pipeline(noop_pipeline).success

    with assert_no_warnings():
        assert execute_pipeline(noop_pipeline, run_config={}).success


def test_no_warnings_execute_pipeline_iterator():
    # flush out unrelated warnings
    list(execute_pipeline_iterator(noop_pipeline))

    with assert_no_warnings():
        list(execute_pipeline_iterator(noop_pipeline))

    with assert_no_warnings():
        list(execute_pipeline_iterator(noop_pipeline, run_config={}))


def test_warnings_execute_pipeline_iterator():
    assert execute_pipeline(noop_pipeline).success

    with mock.patch('warnings.warn') as warn_mock:
        list(execute_pipeline_iterator(noop_pipeline, environment_dict={}))
        warn_mock.assert_any_call(
            '"environment_dict" is deprecated and will be removed in 0.9.0, '
            'use "run_config" instead.',
            stacklevel=5,
        )


def test_pipeline_run():
    pipeline_run_one = PipelineRun(pipeline_name='foo', run_id='1', run_config={})
    assert pipeline_run_one.environment_dict == pipeline_run_one.run_config
    assert pipeline_run_one.environment_dict == {}

    pipeline_run_two = PipelineRun(pipeline_name='foo', run_id='1', run_config={})
    assert pipeline_run_two.environment_dict == pipeline_run_two.run_config
    assert pipeline_run_two.environment_dict == {}
