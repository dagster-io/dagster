from dagster_test.dg_utils.utils import scrub_tox_uv_project_environment


def pytest_configure():
    scrub_tox_uv_project_environment()
