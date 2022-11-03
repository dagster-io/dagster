import tempfile

import pytest

from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._core.test_utils import instance_for_test

from .utils.captured_log_manager import TestCapturedLogManager


def test_compute_log_manager_instance():
    with instance_for_test() as instance:
        assert instance.compute_log_manager
        assert instance.compute_log_manager._instance  # pylint: disable=protected-access


class TestLocalCapturedLogManager(TestCapturedLogManager):
    __test__ = True

    @pytest.fixture(name="captured_log_manager")
    def captured_log_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir_path:
            return LocalComputeLogManager(tmpdir_path)
