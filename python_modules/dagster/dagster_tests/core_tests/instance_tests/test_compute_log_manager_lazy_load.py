from typing import Any, Mapping, Optional

import pytest
from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster._core.test_utils import instance_for_test
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self


class InitFailComputeLogManager(NoOpComputeLogManager, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        super().__init__(inst_data)
        raise Exception("Expected init fail")

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return InitFailComputeLogManager(inst_data=inst_data)


def test_lazy_load():
    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": (
                    "dagster_tests.core_tests.instance_tests.test_compute_log_manager_lazy_load"
                ),
                "class": "InitFailComputeLogManager",
                "config": {},
            }
        }
    ) as instance:
        with pytest.raises(Exception, match="Expected init fail"):
            print(instance.compute_log_manager)  # noqa: T201
