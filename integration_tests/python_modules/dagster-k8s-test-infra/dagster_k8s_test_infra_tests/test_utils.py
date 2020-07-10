from dagster_k8s_test_infra.integration_utils import get_test_namespace


def test_get_test_namespace():
    assert isinstance(get_test_namespace(), str)
