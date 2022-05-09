import os
import shutil

import pytest

import docs_snippets.guides.dagster.dagster_type_factories as example_root
from dagster import check_dagster_type
from dagster.core.errors import DagsterTypeCheckDidNotPass
from docs_snippets.guides.dagster.dagster_type_factories.job_1 import (
    generate_trip_distribution_plot as job_1,
)
from docs_snippets.guides.dagster.dagster_type_factories.job_2 import (
    generate_trip_distribution_plot as job_2,
)
from docs_snippets.guides.dagster.dagster_type_factories.simple_example import (
    set_containing_1,
    set_has_element_type_factory,
)

EBIKE_TRIPS_PATH = os.path.join(example_root.__path__[0], "ebike_trips.csv")


def test_simple_example_one_off():
    assert check_dagster_type(set_containing_1, {1, 2}).success


def test_simple_example_factory():
    set_containing_2 = set_has_element_type_factory(2)
    assert check_dagster_type(set_containing_2, {1, 2}).success


@pytest.fixture(scope="function")
def in_tmpdir(monkeypatch, tmp_path_factory):
    path = tmp_path_factory.mktemp("ebike_trips")
    shutil.copy(EBIKE_TRIPS_PATH, path)
    monkeypatch.chdir(path)


@pytest.mark.usefixtures("in_tmpdir")
def test_job_1_fails():
    with pytest.raises(ValueError):
        job_1.execute_in_process()


@pytest.mark.usefixtures("in_tmpdir")
def test_job_2_no_clean_fails():
    with pytest.raises(DagsterTypeCheckDidNotPass):
        job_2.execute_in_process()


@pytest.mark.usefixtures("in_tmpdir")
def test_job_2_no_clean_succeeds():
    assert job_2.execute_in_process(
        run_config={"ops": {"load_trips": {"config": {"clean": True}}}}
    ).success
    assert os.path.exists("./trip_lengths.png")
