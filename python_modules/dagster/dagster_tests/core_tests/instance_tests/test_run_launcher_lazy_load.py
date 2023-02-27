from typing import Any, Mapping, Optional

import pytest
from dagster._core.launcher import RunLauncher
from dagster._core.test_utils import instance_for_test
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self


class InitFailRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        super().__init__()
        self._inst_data = inst_data
        raise Exception("Expected init fail")

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return InitFailRunLauncher(inst_data=inst_data)

    def launch_run(self, context):
        ...

    def resume_run(self, context):
        ...

    def join(self, timeout=30):
        pass

    def terminate(self, run_id):
        raise NotImplementedError()

    @property
    def supports_resume_run(self):
        return True

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, _run):
        ...


def test_lazy_load():
    with instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.core_tests.instance_tests.test_run_launcher_lazy_load",
                "class": "InitFailRunLauncher",
                "config": {},
            }
        }
    ) as instance:
        with pytest.raises(Exception, match="Expected init fail"):
            print(instance.run_launcher)  # pylint: disable=print-call
