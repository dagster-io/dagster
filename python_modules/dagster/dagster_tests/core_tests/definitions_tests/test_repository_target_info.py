from dagster import RepositoryTargetInfo


def define_pipeline():
    return 1


def test_repository_target_info():
    res = RepositoryTargetInfo.for_pipeline_fn(define_pipeline)
    assert res.python_file == __file__
    assert res.fn_name == 'define_pipeline'
