import pytest
from celery.contrib.testing import worker
from celery.contrib.testing.app import setup_default_app
from dagster_celery.tasks import make_app


@pytest.fixture(scope='session')
def dagster_celery_app():
    app = make_app()
    with setup_default_app(app, use_trap=False):
        yield app


# pylint doesn't understand pytest fixtures
@pytest.fixture(scope='function')
def dagster_celery_worker(dagster_celery_app):  # pylint: disable=redefined-outer-name
    with worker.start_worker(dagster_celery_app, perform_ping_check=False) as w:
        yield w
