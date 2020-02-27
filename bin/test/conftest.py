import pytest

from ..dagster_module import DagsterModule


@pytest.fixture(scope='session')
def dagster_modules():
    return (
        DagsterModule('dagster', is_library=False),
        DagsterModule('dagster-k8s', is_library=True),
    )
